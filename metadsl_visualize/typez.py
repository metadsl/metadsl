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
import warnings

__all__ = ["convert_rule", "TypezRule", "SHOW_MODULE"]

TypezRule = typing.Callable[[metadsl.ExpressionReference], typing.Iterable[Typez]]


def convert_rule(rule: metadsl.Rule) -> TypezRule:
    return _ConvertRule(rule)


@dataclasses.dataclass
class _ConvertRule:
    rule: metadsl.Rule

    def __call__(self, ref: metadsl.ExpressionReference) -> typing.Iterable[Typez]:
        # First yield the initial object
        nodes = convert_to_nodes(ref)
        initial_node_id = str(ref.hash)
        yield Typez(states=States(initial=initial_node_id), nodes=nodes)
        # Then loop through each replacement and export each as a state
        # We make sure not to mutate any older values
        states: typing.List[State] = []
        rule: metadsl.Rule = self.rule  # type: ignore
        for replacement in rule(ref):
            new_nodes = convert_to_nodes(ref)
            # combine nodes
            nodes = {**nodes, **new_nodes}
            # Add a new state
            states = states + [
                State(
                    node=str(ref.hash), rule=replacement.rule, label=replacement.label
                )
            ]
            yield (
                Typez(
                    states=States(initial=initial_node_id, states=states), nodes=nodes
                )
            )


def convert_to_nodes(ref: metadsl.ExpressionReference) -> Nodes:
    """
    Converts an expression into a node mapping and also returns the ID for the top level node.
    """
    expressions = ref.expressions
    nodes: Nodes = {}
    for hash_, expr in expressions.expressions.items():
        node: typing.Union[CallNode, PrimitiveNode]
        value = expr.value
        if isinstance(value, metadsl.Expression):
            children = expr.children
            assert children
            node = CallNode(
                type_params=typevars_to_typeparams(
                    metadsl.typing_tools.get_fn_typevars(value.function)
                )
                or None,
                function=function_or_type_repr(value.function),
                args=[str(a) for a in children.args] or None,
                kwargs={k: str(v) for k, v in children.kwargs.items()} or None,
            )
        else:
            node = PrimitiveNode(
                type=function_or_type_repr(type(value)), repr=repr(value)
            )
        nodes[str(hash_)] = [str(expr.id), node]  # type: ignore
    return nodes


def typevars_to_typeparams(
    typevars: metadsl.typing_tools.TypeVarMapping
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
                metadsl.typing_tools.match_types(
                    metadsl.typing_tools.get_origin_type(tp), tp
                )
            )
            or None,
        )
    return ExternalTypeInstance(repr=function_or_type_repr(tp))


_builtins = inspect.getmodule(int)


SHOW_MODULE = False


def function_or_type_repr(o: typing.Union[typing.Type, typing.Callable]) -> str:
    """
    returns the name of the type or function prefixed by the module name if it isn't a builtin
    """
    if isinstance(o, typing.TypeVar):  # type: ignore
        warnings.warn(
            "Unresolved typevar in type argument, this means the typing is broken",
            RuntimeWarning,
        )
        return repr(o)

    # This is true for `typing.Any`
    if isinstance(o, typing._SpecialForm):
        return repr(o)

    name = o.__qualname__ or o.__name__
    # This is true for objects in typing
    if not name:
        return repr(o)
    if not SHOW_MODULE:
        return name
    module = inspect.getmodule(o)
    if module == _builtins:
        return name
    return f"{module.__name__}.{name}"
