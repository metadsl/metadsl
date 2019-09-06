"""
Meta language for describing DSLs in JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
import dataclasses
from typing import *
import json
import jsonschema
import pathlib
import IPython.core.display
import graphviz

__all__ = [
    "Typez",
    "Definitions",
    "Kind",
    "Function",
    "Type",
    "TypeParameter",
    "DeclaredType",
    "ExternalType",
    "Nodes",
    "CallNode",
    "PrimitiveNode",
    "TypeInstance",
    "DeclaredTypeInstance",
    "ExternalTypeInstance",
    "States",
    "State",
    "TypezDisplay",
]
__version__ = "0.0.0"

with open(pathlib.Path(__file__).parent / "schema.json") as f:
    typez_schema = json.load(f)

# All of these defintions are copied from
# `index.ts` and these two files should be manually
# kept synchronized


@dataclass(frozen=True)
class TypezGraph:
    initial: Optional[str]
    states: List[GraphState]


@dataclass(frozen=True)
class GraphState:
    graph: str
    rule: str
    label: Union[str, None]


def render_graph(node_id: str, nodes: Nodes) -> str:
    """
    Renders a graphviz graph for a node and its descendents
    """
    d = graphviz.Digraph()
    seen: Set[str] = set()

    def process_type_instance(id_: str, instance: TypeInstance):
        if isinstance(instance, ExternalTypeInstance):
            d.node(id_, filter_str(instance.repr))
            return
        d.node(id_, filter_str(instance.type))
        for i, kv in enumerate((instance.params or {}).items()):
            child_id = f"{id_}.{i}"
            k, v = kv
            process_type_instance(child_id, v)
            d.edge(id_, child_id, label=filter_str(k))

    def process_node(id_: str):
        if id_ in seen:
            return
        seen.add(id_)
        node = nodes[id_]
        # If this is a primitive node, we don't need to process anymore
        if isinstance(node, PrimitiveNode):
            d.node(id_, filter_str(node.repr))
            return
        # Otherwise, create the node then add its children
        d.node(id_, filter_str(node.function))
        for child in (node.args or []) + list((node.kwargs or {}).values()):
            d.edge(id_, child)
            process_node(child)
        # Then add the type params for this node
        for i, kv in enumerate((node.type_params or {}).items()):
            k, v = kv
            type_id = f"{id_}.{i}"
            process_type_instance(type_id, v)
            d.edge(id_, type_id, label=filter_str(k))

    process_node(node_id)
    return d.source


def filter_str(n):
    return n.replace("<", "").replace(">", "")


@dataclass(frozen=True)
class Typez:
    definitions: Optional[Definitions] = None
    nodes: Optional[Nodes] = None
    states: Optional[States] = None

    def asdict(self):
        """
        Turns this into a dict, removing keys with null values and
        validating it against the schema.
        """
        dict_ = dataclasses.asdict(
            self,
            dict_factory=lambda entries: {k: v for k, v in entries if v is not None},
        )
        jsonschema.validate(dict_, typez_schema)
        return dict_

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {
            "application/json": self.asdict(),
            "application/x.typez.graph+json": dataclasses.asdict(self.as_graph()),
        }

    def as_graph(self) -> TypezGraph:
        return TypezGraph(
            initial=render_graph(self.states.initial, self.nodes or {})
            if self.states
            else None,
            states=[
                GraphState(
                    graph=render_graph(state.node, self.nodes or {}),
                    rule=state.rule,
                    label=state.label,
                )
                for state in self.states.states or []
            ]
            if self.states
            else [],
        )


Definitions = Dict[str, Union["Kind", "Function"]]


@dataclass(frozen=True)
class Kind:
    params: Optional[List[str]] = None


@dataclass(frozen=True)
class Function:
    params: List[Tuple[str, Type]]
    return_: Type
    type_params: Optional[List[str]] = None
    rest_param: Optional[Tuple[str, Type]] = None


Type = Union["TypeParameter", "DeclaredType", "ExternalType"]


@dataclass(frozen=True)
class TypeParameter:
    param: str


@dataclass(frozen=True)
class DeclaredType:
    type: str
    params: Optional[Dict[str, Type]] = None


@dataclass(frozen=True)
class ExternalType:
    type: str
    repr: str


Nodes = Dict[str, Union["CallNode", "PrimitiveNode"]]


@dataclass(frozen=True)
class CallNode:
    function: str
    type_params: Optional[Dict[str, TypeInstance]] = None
    args: Optional[List[str]] = None
    kwargs: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """
        Make the args and kwargs hashable for easy hasing of the node
        to compute its id
        """
        # Use settattr because it is frozen
        if self.type_params is not None:
            object.__setattr__(self, "type_params", Hashabledict(self.type_params))
        if self.kwargs is not None:
            object.__setattr__(self, "kwargs", Hashabledict(self.kwargs))
        if self.args is not None:
            object.__setattr__(self, "args", Hashablelist(self.args))


@dataclass(frozen=True)
class PrimitiveNode:
    type: str
    repr: str


TypeInstance = Union["DeclaredTypeInstance", "ExternalTypeInstance"]


@dataclass(frozen=True)
class DeclaredTypeInstance:
    type: str
    params: Optional[Dict[str, TypeInstance]] = None

    def __post_init__(self):
        if self.params is not None:
            object.__setattr__(self, "params", Hashabledict(self.params))


@dataclass(frozen=True)
class ExternalTypeInstance:
    repr: str


@dataclass(frozen=True)
class States:
    initial: str
    states: Optional[List["State"]] = None


@dataclass(frozen=True)
class State:
    node: str
    rule: str
    label: Optional[str] = None


@dataclass
class TypezDisplay:
    """
    A display object for typez objects. If you set the `typez` property after calling `display` it will update
    the existing display.
    """

    typez: Typez
    _typez: Typez = dataclasses.field(init=False, repr=False)
    _handle: Optional[IPython.core.display.DisplayHandle] = dataclasses.field(
        default=None, init=False, repr=False
    )

    def _ipython_display_(self):
        self._handle = IPython.core.display.display(self.typez, display_id=True)

    @property  # type: ignore
    def typez(self):
        return self._typez

    @typez.setter
    def typez(self, value: Typez):
        self._typez = value
        if self._handle:
            self._handle.update(self.typez)


class Hashabledict(dict):
    """
    Dict that hashses to its key, value pairs.

    https://stackoverflow.com/a/16162138/907060
    """

    def __hash__(self):
        return hash(frozenset(self.items()))


class Hashablelist(list):
    def __hash__(self):
        return hash(frozenset(self))
