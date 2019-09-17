import json
import html
import copy
import re
from pprint import pformat
from collections import namedtuple
from collections.abc import MutableSequence
from contextlib import contextmanager


object_entry = namedtuple("object_entry", ['objid'])
attr_entry = namedtuple("attr_entry", ["objid", "name"])
flatten_entry = namedtuple("flatten_entry", ['handle'])

object_meta = namedtuple("object_meta", ['cls', 'attrs'])


def _get_attr_entry(obj_entry, attrname):
    return attr_entry(objid=obj_entry.objid, name=attrname)


def _recreate(resmngr, value):
    """Recreate a flattened value into an object.
    """
    if isinstance(value, flatten_entry):
        meta = {
            'resmngr': resmngr,
            'handle': value.handle,
        }
        cls, attrs = resmngr[value.handle]
        value = cls(meta)
    return value


_err_migrate = (
    "Cannot migrate Managed objects between different "
    "ResourceManager instances"
)


def _make_stringify_ctx():
    return {
        'depth': 0,
        # Map object-id to a shorter id.
        'showed': {}
    }


_in_stringify = None


@contextmanager
def stringify_context(obj):
    """A context to indicate that we are nested in a `__str__` or `__repr__`.
    """
    global _in_stringify
    if not _in_stringify:
        _in_stringify = _make_stringify_ctx()
    _in_stringify['depth'] += 1
    showed = _in_stringify['showed']
    objid = obj._obj_handle
    nested = objid in showed
    if not nested:
        showed[objid] = objid.objid
    try:
        yield nested
    finally:
        _in_stringify['depth'] -= 1
        if _in_stringify['depth'] == 0:
            _in_stringify = None


def get_short_id(obj):
    objid = obj._obj_handle
    if _in_stringify:
        return _in_stringify['showed'][objid]
    else:
        return objid


class RedirectAccess(type):
    special_attrs = {'_resmngr', '_obj_handle'}

    def __new__(cls, name, bases, d):
        d['__slots__'] = cls.special_attrs
        return type.__new__(cls, name, bases, d)

    def __init__(cls, name, bases, d):
        type.__init__(cls, name, bases, d)

        def setter(self, k, v):
            if k not in cls.special_attrs:
                entry = _get_attr_entry(self._obj_handle, k)
                if isinstance(v, Managed):
                    v = self._resmngr.flatten(v)
                elif v is None:
                    pass
                elif isinstance(v, (int, float, str)):
                    pass
                elif self._resmngr.is_accepted_types(v):
                    pass
                else:
                    raise ValueError(
                        'cannot use value of type {}'.format(type(v)),
                    )

                try:
                    self._resmngr[entry] = v
                except KeyError:
                    raise AttributeError(k)
                else:
                    old = self._resmngr[self._obj_handle]
                    new = old._replace(attrs=old.attrs | {k})
                    self._resmngr[self._obj_handle] = new
            else:
                super(cls, self).__setattr__(k, v)

        def getter(self, k):
            if k not in cls.special_attrs and not k.startswith('__'):
                entry = _get_attr_entry(self._obj_handle, k)
                try:
                    v = self._resmngr[entry]
                except KeyError:
                    raise AttributeError(
                        "Missing {}.{}".format(type(self).__name__, k),
                    )
                else:
                    return _recreate(self._resmngr, v)
            else:
                return super(cls, self).__getattr__(k)

        def delter(self, k):
            if k not in cls.special_attrs and not k.startswith('__'):
                entry = _get_attr_entry(self._obj_handle, k)
                try:
                    del self._resmngr[entry]
                except KeyError:
                    raise AttributeError(k)
                else:
                    old = self._resmngr[self._obj_handle]
                    new = old._replace(attrs=old.attrs - {k})
                    self._resmngr[self._obj_handle] = new
            else:
                return super(cls, self).__delattr__(k)

        cls.__setattr__ = setter
        cls.__getattr__ = getter
        cls.__delattr__ = delter

    def __call__(cls, _meta_, *args, **kwargs):
        resmngr = _meta_['resmngr']
        obj = object.__new__(cls)
        obj._resmngr = resmngr
        if 'handle' in _meta_:
            obj._obj_handle = _meta_['handle']
        else:
            obj._obj_handle = object_entry(objid=_new_slot(resmngr))
            resmngr[obj._obj_handle] = object_meta(cls=cls, attrs=frozenset())
        return obj


def _new_slot(heap):
    try:
        return heap['__heap_slot__']
    finally:
        heap['__heap_slot__'] += 1


assume_info_is_id0 = "Info object id is assumed to be 0"


class IncompleteStateError(Exception):
        """An error indicating that the ResourceManager cannot be loaded
        from a dictionary because it is incomplete.
        """
        pass


class ResourceManager(object):
    __slots__ = ['_dct', '_infos']
    accepted_types = ()


    @classmethod
    def load_from_dict(cls, dct):
        """Make a new ResourceManager from a dictionary.
        """
        self = cls()
        self._dct = dct
        try:
            infos = self.find_object_by_id(0)
        except KeyError:
            raise IncompleteStateError("Info entry is not available.")
        assert isinstance(infos, Infos), assume_info_is_id0
        self._infos = infos
        return self

    def __init__(self):
        from tict import Tict
        # dictimpl = dict
        dictimpl = Tict
        self._dct = dictimpl()
        self._dct['__heap_slot__'] = 0
        self._infos = self.new(Infos)
        assert self.flatten(self._infos).handle.objid == 0, assume_info_is_id0

    def __getitem__(self, k):
        return self._dct[k]

    def __setitem__(self, k, v):
        self._dct[k] = v

    def __delitem__(self, k):
        del self._dct[k]

    @property
    def infos(self):
        return self._infos

    def is_accepted_types(self, instance):
        accepted = self.accepted_types
        return accepted and isinstance(instance, accepted)

    def new(self, typ_, *args, **kwargs):
        if not issubclass(typ_, Managed):
            raise TypeError("{} is not a subclass of {}".format(typ_, Managed))
        obj = typ_({'resmngr': self})
        obj.init(*args, **kwargs)
        return obj

    def new_list(self, initializer=()):
        lst = self.new(ManagedList)
        for it in initializer:
            lst.append(it)
        return lst

    def clone(self):
        return copy.deepcopy(self)

    def flatten(self, managed_obj):
        """Flatten a Managed object into a handle.
        """
        if not isinstance(managed_obj, Managed):
            raise ValueError('expecting an instance of {}'.format(Managed))
        if managed_obj._resmngr is not self:
            raise ValueError(_err_migrate)
        return flatten_entry(handle=managed_obj._obj_handle)

    def inflate(self, handle):
        """Recreate a Managed object from a handle.
        """
        if not isinstance(handle, flatten_entry):
            raise ValueError(
                'expecting an instance of {}'.format(flatten_entry),
            )
        return _recreate(self, handle)

    def dump(self):
        return pformat(self._dct)

    def iter_attributes(self):
        """Returns an iterator that yields key-value pairs which corresponds
        to attribute entries.
        """
        return iter((k, v) for k, v in self._dct.items()
                    if isinstance(k, attr_entry))

    def replace_all(self, old, new):
        """Replace all references to Managed object *old* to *new*.

        Returns
        -------
        replaced_count : int
        """
        replmap = {}
        hdl = self.flatten(new)
        oldhdl = self.flatten(old)
        for k, v in self.iter_attributes():
            if oldhdl == v:
                replmap[k] = hdl
        self._dct.update(replmap)
        return len(replmap)

    def iter_objects(self):
        """Returns an iterator that yields all the Managed objects.
        """
        for k in self._dct:
            if isinstance(k, object_entry):
                yield self.find_object_by_id(k.objid)

    def iter_referers(self, obj):
        """Returns an iterator that yields all the referer of an object.
        Precisely, it yields a 2-tuple of ``(referer_object, attrname)``
        """
        hdl = self.flatten(obj)
        for k, v in self.iter_attributes():
            if v == hdl:
                referer_id = k.objid
                referer = self.find_object_by_id(referer_id)
                attrname = k.name
                yield _iter_referers_result(referer, attrname)

    def iter_referents(self, obj):
        """Returns an iterator that yields all the referents of an object.
        Precisely, it yields a 2-tuple of ``(attrname, referent_object)``
        """
        for k in self.get_attributes(obj):
            val = self[_get_attr_entry(obj._obj_handle, k)]
            if isinstance(val, flatten_entry):
                val = self.inflate(val)
            yield _iter_referents_result(k, val)

    def get_attributes(self, obj):
        """Returns the attributes associated with a *obj*.
        """
        hdl = obj._obj_handle
        return tuple(self[hdl].attrs)

    def find_object_by_id(self, objid):
        """Get the object using given the object ID, *objid*.
        """
        return self.inflate(flatten_entry(handle=object_entry(objid)))

    def visualize_raw(self):
        """
        Returns
        -------
        (nodes, edges) : (List[Dict], List[Dict])

        """
        # Draw nodes
        nodes = []
        managed_attrs = []
        labelfmt = ('<TD PORT={!r}>{}<BR/>'
                    '<FONT POINT-SIZE="8pt">{} :: {}</FONT></TD>')
        for obj in self.iter_objects():
            src = str(obj._obj_handle)

            labelbuf = [
                '{}@{}'.format(
                    type(obj).__name__,
                    obj._obj_handle.objid
                ),
            ]

            def attr_sort(name):
                m = re.match(r"^_\d+$", name)
                if m is None:
                    return name
                else:
                    return '{:08x}'.format(int(name[1:]))

            arglist = sorted(self.get_attributes(obj), key=attr_sort)
            for attr in arglist:
                attrval = getattr(obj, attr, None)
                if attrval is None:
                    # Allow incomplete graph.
                    # Note: useful in animating revisions.
                    continue
                elif isinstance(attrval, Managed):
                    dst = "{}:this".format(attrval._obj_handle)
                    managed_attrs.append(('{}:{}'.format(src, attr), dst))
                    labelbuf.append('<TD PORT={!r}>{}</TD>'.format(attr, attr))
                else:
                    # Non-managed values
                    desc = repr(attrval)
                    label = labelfmt.format(
                        attr,
                        attr,
                        html.escape(desc),
                        type(attrval).__name__,
                    )
                    labelbuf.append(label)

            # if isinstance(obj, ManagedList) and len(labelbuf) > 8:
            #     head, tail = labelbuf[0], labelbuf[1:]
            #     tail = ''.join(map('<TR>{}</TR>'.format, tail))
            #     label = '''<
            #         <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
            #         <TR><TD PORT="this">{}</TD></TR>
            #         {}</TABLE>
            #     >'''.format(head, tail)
            # else:
            head, tail = labelbuf[0], ''.join(labelbuf[1:])
            if tail:
                tail = "<TR>{}</TR>".format(tail)
            label = '''<
                <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                <TR><TD PORT="this" COLSPAN="{}">{}</TD></TR>
                {}</TABLE>
            >'''.format(max(1, len(labelbuf) - 1), head, tail)

            nodes.append({
                'name': src,
                'label': label,
                'shape': 'plaintext'
            })

        # Draw edges
        edges = []
        for src, dst in managed_attrs:
            edges.append({
                'tail_name': src,
                'head_name': dst,
            })

        return nodes, edges

    def visualize(self):
        """Print a DOT graph
        """
        nodes, edges = self.visualize_raw()
        return graphviz_visualize(nodes, edges)

    def internal_dict(self):
        """Returns the internal dictionary
        """
        return self._dct.copy()


def graphviz_visualize(nodes, edges):
    """Visualize nodes and edges as with graphviz

    Note: requires the `graphviz` (the python package)
    """
    import graphviz as gv

    g = gv.Digraph()
    for node in nodes:
        g.node(**node)
    for edge in edges:
        g.edge(**edge)
    return g


def graphviz_diff(last_nodes, last_edges, nodes, edges):
    """Highlight the difference between the last and current nodes and edges.
    """
    oldnodes = {n['name']: n for n in last_nodes}
    oldedges = {info['tail_name']: info['head_name'] for info in last_edges}
    for n in nodes:
        # New node
        if n['name'] not in oldnodes:
            n['color'] = 'blue'
        # Node label changed
        elif n['label'] != oldnodes[n['name']]['label']:
            n['color'] = 'orange'
    for e in edges:
        # New edge
        if e['head_name'] != oldedges.get(e['tail_name'], None):
            e['color'] = 'blue'
    return nodes, edges


def graphviz_render_revisions(resmngr, since=None, backend='d3', attrs={}):
    """Render revisions applied to **resmngr** start from **since** revision.


    Parameters
    ----------
    resmngr :
        A ResourceManager backed with Tict.
    since : tict.SavedState or None
    backend : str; defaults to "d3"
        Available options are: "d3", and "gv".
    attrs: dict; defaults to ``{}``
        For attaching additional keyword arguments to the backend.
    """
    journals = resmngr.internal_dict()

    last_nodes, last_edges = [], []
    dots = []
    for i, rev in enumerate(journals.revisions(since=since)):
        # Load dictionary as plain ResourceManager.
        # Note, it's row-polymorphic
        try:
            rev_res = ResourceManager.load_from_dict(rev)
        except IncompleteStateError:
            continue
        nodes, edges = rev_res.visualize_raw()
        diffed = graphviz_diff(last_nodes, last_edges, nodes, edges)
        g = graphviz_visualize(*diffed)
        # g.render(filename=name, format='gv', directory='anim', cleanup=True)
        dots.append(str(g))
        last_nodes, last_edges = nodes, edges

    backends = {
        'd3': _graphviz_d3_revs_backend,
        'gv': _graphviz_revs_backend,
    }
    return backends[backend](dots, **attrs)


def _graphviz_revs_backend(dots, name_prefix='resmngr_revs', dir='anim',
                           format='gv'):
    """Graphviz revision rendering backend
    """
    import graphviz as gv

    filenames = []
    places = len(str(len(dots)))
    for i, src in enumerate(dots):
        g = gv.Source(src)
        name = '{{}}_{{:0{}}}'.format(places).format(name_prefix, i)
        path = g.render(
            filename=name, format=format, directory=dir, cleanup=True,
        )
        filenames.append(path)
    return filenames


def _graphviz_d3_revs_backend(dots):
    """D3 revision rendering backend
    """
    # See https://github.com/magjac/d3-graphviz
    with open('d3dot_template.html') as fin:
        template = fin.read()
    js_dots = map(json.dumps, map(lambda x: x.splitlines(), dots))
    return template.replace('/*replaceme*/', ',\n'.join(js_dots))


_iter_referers_result = namedtuple(
    '_iter_referers_result', ['referer', 'attrname'],
)
_iter_referents_result = namedtuple(
    '_iter_referents_result', ['attrname', 'referent'],
)


class Managed(metaclass=RedirectAccess):
    """Instances of ``Managed`` must be created by ``ResourceManager.new()``.

    Subclasses should not define ``__new__`` or ``__init__``.
    Custom initialization is defined in ``init``, which return value is
    ignored.
    """
    def init(self):
        pass

    def __repr__(self):
        with stringify_context(self) as nested:
            cls = type(self).__qualname__
            if nested:
                return "@{}".format(get_short_id(self))
            else:
                attrs = self._resmngr.get_attributes(self)
                pairs = ['{}={!r}'.format(k, getattr(self, k))
                         for k in sorted(attrs)]
                return "{}@{}({})".format(
                    cls, get_short_id(self), ', '.join(pairs),
                )


class Infos(Managed):
    pass


class ManagedList(Managed):
    def init(self, values=()):
        self._count = 0
        for v in values:
            self.append(v)

    def append(self, item):
        slot = self._count
        self._count += 1
        setattr(self, '_{}'.format(slot), item)

    def extend(self, iterable):
        for i in iterable:
            self.append(i)

    def pop(self):
        item = self[-1]
        self._count -= 1
        name = '_{}'.format(self._count)
        delattr(self, name)
        return item

    def __len__(self):
        return self._count

    def __setitem__(self, idx, item):
        idx = range(self._count)[idx]
        setattr(self, '_{}'.format(idx), item)

    def __getitem__(self, idx):
        idx = range(self._count)[idx]
        return getattr(self, '_{}'.format(idx))

    def __repr__(self):
        with stringify_context(self) as nested:
            cls = type(self).__qualname__
            if nested:
                return "@{}".format(get_short_id(self))
            else:
                return "{}@{}({})".format(
                    cls, get_short_id(self), repr(list(self)),
                )


MutableSequence.register(ManagedList)


# ------------- TEST -------------------

class Test(Managed):
    def init(self):
        self.a = 1
        self.a = 2
        self.node = self._resmngr.new(Node, 123)
        self.more = self._resmngr.new_list([
            self._resmngr.new(Node, 100),
            self._resmngr.new(Node, 200),
        ])


class Node(Managed):
    def init(self, v):
        self.b = v


def main():
    s = ResourceManager()
    t = s.new(Test)
    print('t.a =', t.a)

    print(s.dump())

    print(hasattr(t, '__dict__'))

    print('t.node =', t.node)
    t.node.b = 321
    print('t.node.b =', t.node.b)

    # print(pickle.loads(pickle.dumps(s)))
    # print(pickle.loads(pickle.dumps(t)))

    print(s.dump())

    print(t.more[0].b)
    print(t.more[1].b)


if __name__ == '__main__':
    main()

