"""
Integeration with typez, to translate a "Rule" into a something that takes returns an iterable of
typez object we can use to display as we go.
"""

import dataclasses
import functools
import inspect
import types
import typing
import warnings

import metadsl
import typing_inspect
from typez import *

__all__ = ["ExpressionDisplay", "SHOW_MODULE"]


@functools.singledispatch
def metadsl_str(value: object) -> str:
    return str(value)


@metadsl_str.register
def metadsl_str_fn(fn: types.FunctionType) -> str:
    if not SHOW_TYPES or not hasattr(fn, "__scoped_typevars__"):
        return str(fn)
    return f"{fn} (scoped_typevars={fn.__scoped_typevars__})"  # type: ignore


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
        old_nodes = self.typez_display.typez.nodes or []
        old_node_ids = set(node.id for node in old_nodes)
        self.typez_display.typez = dataclasses.replace(
            self.typez_display.typez,
            # Must keep in topo order with the root expression at the end
            nodes=(
                old_nodes + [node for node in new_nodes if node.id not in old_node_ids]
            ),
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
    Converts an expression into a node mapping.
    """
    nodes: Nodes = []
    for ref in ref.descendents:
        node: typing.Union[CallNode, PrimitiveNode]
        value = ref.expression
        if isinstance(value, metadsl.Expression):
            children = ref.children
            func_str = function_or_type_repr(value.function)
            node = CallNode(
                id=str(ref.hash),
                type_params=typevars_to_typeparams(
                    metadsl.typing_tools.get_fn_typevars(value.function)
                )
                or None,
                function=f"{func_str}: {value._type_str}" if SHOW_TYPES else func_str,
                args=[str(a) for a in children.args] or None,
                kwargs={k: str(v) for k, v in children.kwargs.items()} or None,
            )
        else:
            node = PrimitiveNode(
                id=str(ref.hash),
                type=function_or_type_repr(type(value)),
                repr=metadsl_str(value),
            )
        nodes.append(node)
    return nodes


def typevars_to_typeparams(
    typevars: metadsl.typing_tools.TypeVarMapping,
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

WARN_ON_TYPEVAR = False


def function_or_type_repr(o: typing.Union[typing.Type, typing.Callable]) -> str:
    """
    returns the name of the type or function prefixed by the module name if it isn't a builtin
    """
    if isinstance(o, typing.TypeVar):  # type: ignore
        if WARN_ON_TYPEVAR:
            warnings.warn(
                "Unresolved typevar in type argument, this means the typing is broken",
                RuntimeWarning,
            )
            return repr(o)
        else:
            raise RuntimeError("Unresolved typevar in type argument")

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
    assert module
    return f"{module.__name__}.{name}"
