"""
Integeration with typez, to translate a "Rule" into a something that takes returns an iterable of
typez object we can use to display as we go.
"""

from typez import *
import metadsl
import typing
import inspect
import dataclasses
import typing_inspect

__all__ = ["convert_rule", "TypezRule"]

TypezRule = typing.Callable[[object], typing.Iterable[typing.Tuple[object, Typez]]]


def convert_rule(rule: metadsl.Rule[typing.Any]) -> TypezRule:
    return _ConvertRule(rule)


@dataclasses.dataclass
class _ConvertRule:
    rule: metadsl.Rule[typing.Any]

    def __call__(self, obj: object) -> typing.Iterable[typing.Tuple[object, Typez]]:
        # First yield the initial object
        initial_node_id, nodes = convert_to_nodes(obj)
        yield (obj, Typez(states=States(initial=initial_node_id), nodes=nodes))
        # Then loop through each replacement and export each as a state
        # We make sure not to mutate any older values
        states: typing.List[State] = []
        for replacement in self.rule(obj):  # type: ignore
            node_id, new_nodes = convert_to_nodes(replacement.result)
            # combine nodes
            nodes = {**nodes, **new_nodes}
            # Add a new state
            states = states + [
                State(node=node_id, rule=replacement.rule, label=replacement.label)
            ]
            yield (
                replacement.result,
                Typez(
                    states=States(initial=initial_node_id, states=states), nodes=nodes
                ),
            )


def convert_to_nodes(expr: object) -> typing.Tuple[str, Nodes]:
    """
    Converts an expression into a node mapping and also returns the ID for the top level node.
    """
    if isinstance(expr, metadsl.Expression):
        nodes: Nodes = {}
        args: typing.List[str] = []
        kwargs: typing.Dict[str, str] = {}
        for arg in expr.args:
            arg_id, arg_nodes = convert_to_nodes(arg)
            args.append(arg_id)
            nodes.update(arg_nodes)
        for k, v in expr.kwargs.items():
            kwarg_id, kwarg_nodes = convert_to_nodes(v)
            kwargs[k] = kwarg_id
            nodes.update(kwarg_nodes)

        # Set the node ID to be the hash of the node
        node = CallNode(
            type_params=typevars_to_typeparams(metadsl.get_fn_typevars(expr.function))
            or None,
            function=function_or_type_repr(expr.function),
            args=args or None,
            kwargs=kwargs or None,
        )
        node_id = str(hash(node))
        nodes[node_id] = node
        return node_id, nodes

    type_ = function_or_type_repr(type(expr))
    # We try to use the has of an object, if we can,
    # otherwise, if its mutable and has no hash, we use its id
    try:
        node_id = str(hash((type_, expr)))
    except TypeError:
        node_id = str(hash((type_, id(expr))))
    return (node_id, {node_id: PrimitiveNode(type=type_, repr=repr(expr))})


def typevars_to_typeparams(
    typevars: metadsl.TypeVarMapping
) -> typing.Dict[str, TypeInstance]:
    return {
        var.__name__: type_to_typeinstance(tp)  # type: ignore
        for var, tp in typevars.items()
    }


def type_to_typeinstance(tp: typing.Type) -> TypeInstance:
    """
    Converts a python type to the type instance, by folding through it
    """
    if issubclass(tp, metadsl.Expression):
        return DeclaredTypeInstance(
            type=function_or_type_repr(typing_inspect.get_origin(tp) or tp),
            params=typevars_to_typeparams(
                metadsl.match_types(metadsl.get_origin_type(tp), tp)
            )
            or None,
        )
    return ExternalTypeInstance(repr=function_or_type_repr(tp))


_builtins = inspect.getmodule(int)


def function_or_type_repr(o: typing.Union[typing.Type, typing.Callable]) -> str:
    """
    returns the name of the type or function prefixed by the module name if it isn't a builtin
    """
    module = inspect.getmodule(o)
    name = o.__qualname__ or o.__name__
    # This is true for objects in typing
    if not name:
        return repr(o)
    if module == _builtins:
        return name
    return f"{module.__name__}.{name}"
