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


__all__ = ["Typez", "TypezDisplay"]
__version__ = "0.0.0"

with open(pathlib.Path(__file__).parent / "schema.json") as f:
    typez_schema = json.load(f)

# All of these defintions are copied from
# `index.ts` and these two files should be manually
# kept synchronized


@dataclass
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
        return {"application/json": self.asdict()}


Definitions = Dict[str, Union["Kind", "Function"]]


@dataclass
class Kind:
    params: Optional[List[str]] = None


@dataclass
class Function:
    params: List[Tuple[str, Type]]
    return_: Type
    type_params: Optional[List[str]] = None


Type = Union["TypeParameter", "DeclaredType", "ExternalType"]


@dataclass
class TypeParameter:
    param: str


@dataclass
class DeclaredType:
    type: str
    params: Optional[List[Type]] = None


@dataclass
class ExternalType:
    type: str
    repr: str


Nodes = Dict[str, Union["CallNode", "PrimitiveNode"]]


@dataclass
class CallNode:
    function: str
    type_params: Optional[List[TypeInstance]] = None
    args: Optional[List[str]] = None
    kwargs: Optional[Dict[str, str]] = None


@dataclass
class PrimitiveNode:
    type: str
    repr: str


TypeInstance = Union["DeclaredTypeInstance", "ExternalTypeInstance"]


@dataclass
class DeclaredTypeInstance:
    type: str
    params: Optional[List[TypeInstance]] = None


@dataclass
class ExternalTypeInstance:
    repr: str


States = List["State"]


@dataclass
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
