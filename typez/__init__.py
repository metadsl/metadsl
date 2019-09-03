"""
Meta language for describing DSLs in JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import *
import json
import jsonschema
import pathlib
import IPython.core.display


__all__ = ["Typez"]
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

    def __post_init__(self):
        jsonschema.validate(asdict(self), typez_schema)


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


class TypezDisplay(IPython.core.display.DisplayObject):
    """
    Modified from 
    https://github.com/ipython/ipython/blob/91d36d325aff4990062901556aa9581d2b22c897/IPython/core/display.py#L764
    """

    def __init__(self, typez: Typez):
        self._typez = typez

    def _repr_mimebundle_(self):
        return {"application/json": asdict(self.typez)}

    def display(self):
        self.display_id = IPython.core.display.display(self, display_id=True)

    def update(self):
        IPython.core.display.display(self, display_id=self._display_id, update=True)

    @property
    def typez(self):
        return self._typez

    @typez.setter
    def typez(self, value):
        self._typez = value
        self.update()
