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

__all__ = ["ExpressionDisplay", "SHOW_MODULE"]


@dataclasses.dataclass
class ExpressionDisplay:
    ref: metadsl.ExpressionReference
    typez_display: TypezDisplay = dataclasses.field(
        default_factory=lambda: TypezDisplay(Typez())
    )

    def __post_init__(self):
        ref = self.ref
        nodes = convert_to_nodes(ref)
        initial_node_id = str(ref.hash)
        self.typez_display.typez = Typez(
            states=States(initial=initial_node_id), nodes=nodes
        )

    def update(self, rule: str, label: typing.Optional[str] = None):
        new_nodes = convert_to_nodes(self.ref)
        self.typez_display.typez = dataclasses.replace(
            self.typez_display.typez,
            nodes={**(self.typez_display.typez.nodes or {}), **new_nodes},
            states=dataclasses.replace(
                self.typez_display.typez.states,
                states=[
                    *(
                        self.typez_display.typez.states.states or []
                        if self.typez_display.typez.states
                        else []
                    ),
                    State(node=str(self.ref.hash), rule=rule, label=label),
                ],
            ),
        )

    def _ipython_display_(self):
        self.typez_display._ipython_display_()


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
