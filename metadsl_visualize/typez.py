"""
Integeration with typez, to translate a "Rule" into a something that takes returns an iterable of
typez object we can use to display as we go.
"""

import base64
import dataclasses
import functools
import importlib
import inspect
import pickle
import types
import typing
import warnings

import black
import metadsl
import typing_inspect
from metadsl.expressions import Expression
from metadsl.normalized import Graph, Hash
from metadsl.typing_tools import BoundInfer, Infer
from metadsl_rewrite import *

from typez import *
from typez import FunctionValue

__all__ = [
    "ExpressionDisplay",
    "SHOW_MODULE",
    "expr_to_json_value",
    "json_value_to_expr",
]


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
        self.typez_display.typez = expression_ref_to_typez(self.ref)

    def update(self, result: Result):
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
                    State(
                        node=str(self.ref.hash),
                        rule=result.name,
                        label=result.label,
                        logs=result.logs,
                    ),
                ],
            ),
        )

    def _ipython_display_(self):
        self.typez_display._ipython_display_()


black_file_mode = black.FileMode(line_length=40)


def expression_ref_to_typez(
    ref: metadsl.ExpressionReference, save_pickle=False
) -> Typez:
    """
    Converts an expression reference to a typez.
    """
    nodes = convert_to_nodes(ref, save_pickle=save_pickle)
    initial_node_id = str(ref.hash)
    return Typez(states=States(initial=initial_node_id), nodes=nodes)


def convert_to_nodes(ref: metadsl.ExpressionReference, save_pickle=False) -> Nodes:
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
                type=type_to_typeinstance(type(value)),
                function=black.format_str(
                    f"{func_str}\n{value._type_str}" if SHOW_TYPES else func_str,
                    mode=black_file_mode,
                ),
                function_value=expression_to_function_value(value),
                args=[str(a) for a in children.args] or None,
                kwargs={k: str(v) for k, v in children.kwargs.items()} or None,
            )
        else:
            node = PrimitiveNode(
                id=str(ref.hash),
                type=function_or_type_repr(type(value)),
                repr=metadsl_str(value),
                python_pickle=pickle_string(value) if save_pickle else None,
            )
        nodes.append(node)
    return nodes


def expression_to_function_value(expr: metadsl.Expression) -> FunctionValue:
    """
    Converts an expression to a FunctionValue.
    """
    fn = expr.function
    assert isinstance(fn, (BoundInfer, Infer))
    return FunctionValue(
        module=fn.__module__,
        name=fn.fn.__name__,
        class_=fn.owner.__name__ if isinstance(fn, BoundInfer) else None,
    )


def function_value_to_fn(fv: FunctionValue) -> types.FunctionType:
    v: typing.Any = importlib.import_module(fv.module)
    if fv.class_ is not None:
        v = getattr(v, fv.class_)
    return getattr(v, fv.name)


def pickle_string(value: object) -> str:
    """
    Returns the object pickled with Python protocol 5 pickle, encoded as a string
    """
    return base64.b64encode(pickle.dumps(value, protocol=5)).decode("ascii")


def load_pickle(v: str) -> object:
    return pickle.loads(base64.b64decode(v))


def expr_to_json_value(expr: metadsl.Expression) -> dict:
    """
    Converts an expression to a JSON value, suitable to be serialized to a string.
    """
    expr_ref = metadsl.ExpressionReference.from_expression(expr)
    return expression_ref_to_typez(expr_ref, save_pickle=True).asdict()


def json_value_to_expr(value: dict) -> metadsl.Expression:
    """
    Converts a JSON value to an expression.
    """
    typez = Typez.from_dict(value)
    graph = Graph()
    assert typez.nodes
    for node in typez.nodes:
        if isinstance(node, PrimitiveNode):
            assert node.python_pickle
            expression = load_pickle(node.python_pickle)
        else:
            expression = type_instance_to_type(node.type)(
                # TODO: replace typevars as well
                function=function_value_to_fn(node.function_value),
                args=[graph._lookup(Hash(a))["expression"] for a in node.args or []],
                kwargs={
                    k: graph._lookup(Hash(v))["expression"]
                    for k, v in (node.kwargs or {}).items()
                },
            )
        graph.add_vertex(expression=expression, name=node.id)
    assert typez.states
    return graph._lookup(Hash(typez.states.initial))["expression"]

def type_instance_to_type(type_instance: TypeInstance) -> type:
    """
    Converts a type instance to a type.
    """
    tp = getattr(importlib.import_module(type_instance.module), type_instance.name)
    # TODO: replace typevars as well
    return tp

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
            name=tp.__name__,
            module=tp.__module__,
            params=typevars_to_typeparams(
                metadsl.typing_tools.match_types(
                    metadsl.typing_tools.get_origin_type(tp), tp
                )
            )
            or None,
        )
    return ExternalTypeInstance(
        repr=function_or_type_repr(tp), name=tp.__name__, module=tp.__module__
    )


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
