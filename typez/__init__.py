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
    "SHOW_TYPES",
    "TypeInstance",
    "DeclaredTypeInstance",
    "ExternalTypeInstance",
    "States",
    "State",
    "TypezDisplay",
]
__version__ = "0.3.0"

SHOW_TYPES = False

# with open(pathlib.Path(__file__).parent / "schema.json") as f:
#     typez_schema = json.load(f)

# All of these defintions are copied from
# `index.ts` and these two files should be manually
# kept synchronized


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
        # jsonschema.validate(dict_, typez_schema)
        return dict_

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {"application/x.typez+json": self.asdict()}

    def __post_init__(self):
        """
        Validate that nodes are in topo order, with root at the end.
        """
        return
        if not self.nodes:
            return
        seen: Set[str] = set()
        for node in self.nodes:
            assert node.id not in seen
            seen.add(node.id)
            if not isinstance(node, CallNode):
                return
            for child_id in (node.args or []) + list((node.kwargs or {}).values()):
                assert child_id in seen


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


# TODO: Rename to expression
Nodes = List[Union["CallNode", "PrimitiveNode"]]


@dataclass(frozen=True)
class CallNode:
    id: str
    function: str
    type_params: Optional[Dict[str, TypeInstance]] = None
    args: Optional[List[str]] = None
    kwargs: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """
        Make the args and kwargs hashable for easy hashing of the node
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
    id: str
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
