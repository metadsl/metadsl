"""
Normalized expressions, for deduping and single replacements.
"""
from __future__ import annotations
import dataclasses
import typing
import itertools
import collections
import functools
import IPython.core.display
import igraph

from .expressions import *


__all__ = [
    "ExpressionReference",
    "Children",
    "Hash",
    "hash_value",
]

Hash = typing.NewType("Hash", str)


class Graph(igraph.Graph):
    """
    Graph of all expression



    Vertex attributes:
    * `name`: string of hash of expression or None if not computed yet
    * `expression`: expression object

    Edge Attributes:
    * `index`: int or string
    """

    def __init__(self, expr: object):
        super().__init__(directed=True)

        self.fully_add_expression(expr, None)
        self.assert_integrity()

    def _repr_svg_(self):
        return self.plot_custom()._repr_svg_()

    def plot_custom(self):
        return igraph.plot(
            self,
            layout=self.layout_sugiyama(),
            vertex_label=[
                f'{v.index}: {v["expression"].function if isinstance(v["expression"], Expression) else v["expression"]}'
                for v in self.vs
            ],
            edge_label=self.es["index"],
            # vertex_shape="hidden",
        )

    def fully_add_expression(
        self,
        expr: object,
        replace: typing.Optional[typing.Tuple[Hash, object]],
        *parent_ids: int,
    ) -> Hash:
        # should never be a child of one of its parents, or else we have a cycle
        assert id(expr) not in parent_ids
        children = frozenset(
            (
                index,
                self.fully_add_expression(
                    child_expression, replace, id(expr), *parent_ids
                ),
            )
            for index, child_expression in expression_children(expr)
        )
        hash_ = Hash(
            str(
                hash(
                    (
                        expr.function
                        if isinstance(expr, Expression)
                        else hash_value(expr),
                        children,
                    )
                )
            )
        )
        # If we are replacing a hash with a new expression and this is the hash of current expression, use the new one instead
        # This means we have added a bunch of nodes we dont need possibly, so we can delete those at the end
        if replace and hash_ == replace[0]:
            return self.fully_add_expression(replace[1], None, *parent_ids)
        try:
            self.lookup(hash_)
        except ValueError:
            v = self.add_vertex(expression=expr, name=hash_)

            for index, child_hash in children:
                assert isinstance(expr, Expression)
                child_v = self.lookup(child_hash)
                self.add_edge(v, child_v, index=index)
                if isinstance(index, int):
                    expr.args[index] = child_v["expression"]
                else:
                    expr.kwargs[index] = child_v["expression"]
        return Hash(hash_)

    def lookup(self, hash_: Hash) -> igraph.Vertex:
        return self.vs.find(name=hash_)

    def replace_root(self, expr: object):
        self.delete_vertices(self.vs)
        self.fully_add_expression(expr, None)
        self.assert_integrity()

    def replace_child(self, expr: object, prev_index: int) -> None:
        # Compute previous hash on the fly instead of passing it in b/c even though previous index
        # must stay constant, the previous hash could have changed between we created this sub-graph
        # and after the rule when we are replacing the expression
        root_expression = self.root_vertex["expression"]

        prev_expr = self.vs[prev_index]["expression"]
        # clear graph
        self.delete_vertices(self.vs)
        prev_hash = self.fully_add_expression(prev_expr, None)

        self.delete_vertices(self.vs)
        new_hash = self.fully_add_expression(root_expression, (prev_hash, expr))
        # Remove all vertice not children of new root node
        self.delete_vertices(
            set(self.vs.indices) - set(self.subcomponent(new_hash, igraph.OUT))
        )
        self.assert_integrity()

    def assert_integrity(self):
        assert self.is_dag()
        # Verify that this is one connected graph (not multiple roots)
        assert self.is_connected(igraph.WEAK)

        # Assert hashes and ids are unique
        hashes = self.vs["name"]
        assert len(hashes) == len(set(hashes))
        # assert edges are unique, with respect to source
        edges = [(e.source, e["index"]) for e in self.es]
        assert len(edges) == len(set(edges))

        for v in self.vs:
            expr = v["expression"]
            for e in v.out_edges():
                idx = e["index"]
                child_expr = (
                    expr.args[idx] if isinstance(idx, int) else expr.kwargs[idx]
                )
                assert id(child_expr) == id(e.target_vertex["expression"])

    @property
    def root_vertex(self) -> igraph.Vertex:
        return self.vs.select(_indegree_eq=0)[0]


@dataclasses.dataclass
class ExpressionReference:
    """
    This is a data structure that holds onto a graph of expression
    and has a pointer to one node, to represent it.
    """

    _graph: Graph
    # Top level vertex if the top level is not root, else None
    _optional_index: typing.Optional[int]

    @classmethod
    def from_expression(cls, expr: object) -> ExpressionReference:
        """
        Create a new reference from an expression
        """
        graph = Graph(expr)
        # top level expression will be first added vertex
        return cls(graph, None)

    @property
    def _is_root(self):
        return self._optional_index is None

    def replace(self, new_expression: object) -> None:
        """
        Replace this expression with a new one
        """

        if self._is_root:
            self._graph.replace_root(new_expression)
        else:
            self._graph.replace_child(
                new_expression, typing.cast(int, self._optional_index)
            )
            # Reset index after replacing b/c we don't know index of newly replaced child
            # (we could, but not sure we need it since we only replace once then through this object away)
            self._optional_index = None

    @property
    def _index(self) -> int:
        return self._graph.root_vertex.index if self._is_root else self._optional_index

    @property
    def _vertex(self) -> igraph.Vertex:
        return self._graph.vs[self._index]

    @property
    def hash(self) -> Hash:
        """
        Returns the Hash of the top level expression
        """
        return Hash(self._vertex["name"])

    @property
    def expression(self) -> object:
        """
        Returns the expression this references
        """
        return self._vertex["expression"]

    @property
    def children(self) -> Children:
        """
        Returns the direct children of this node if it has any.
        """
        args = {}
        kwargs = {}
        for e in self._graph.es[self._graph.incident(self.hash, igraph.OUT)]:
            index = e["index"]
            target_hash = e.target_vertex["name"]
            if isinstance(index, int):
                args[index] = target_hash
            else:
                kwargs[index] = target_hash
        return Children(
            kwargs=kwargs,
            args=tuple(
                id_ for index, id_ in sorted(args.items(), key=lambda kv: kv[0])
            ),
        )

    @property
    def descendents(self) -> typing.Iterable[ExpressionReference]:
        """
        Returns all nodes of this expression reference. If any of them
        get their expression replaced, it will replace that sub-node of this expression.

        If this is the root node, will return them in topo order, otherwise will be arbitrary
        """
        # If we are the root node return all topological with root nodes last
        if self._is_root:
            indices = self._graph.topological_sorting(igraph.IN)
        # Otherwise return all subcomponents
        else:
            indices = self._graph.subcomponent(self._optional_index, igraph.OUT)
        return [ExpressionReference(self._graph, i) for i in indices]


@dataclasses.dataclass(frozen=True)
class Children:
    args: typing.Tuple[Hash, ...]
    kwargs: typing.Dict[str, Hash]

    def _references(
        self,
    ) -> typing.Iterable[typing.Tuple[typing.Union[str, int], Hash]]:
        return itertools.chain(enumerate(self.args), self.kwargs.items())


@functools.singledispatch
def hash_value(value: object) -> int:
    """
    Computes some hash for a value that should be stable. Either use the built in hash, or if we cannot
    (like the object is mutable) then use the id.

    It's a single dispatch function so that you can register custom hashes for objects you don't control.
    """
    try:
        return hash((type(value), value))
    except TypeError:
        return hash((type(value), id(value)))


def expression_children(
    expr: object,
) -> typing.Iterable[typing.Tuple[typing.Union[int, str], object]]:
    if not isinstance(expr, Expression):
        return
    yield from enumerate(expr.args)
    yield from expr.kwargs.items()
