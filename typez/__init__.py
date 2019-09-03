"""
Meta language for describing DSLs in JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import *
import json
import jsonschema

__all__ = ["Typez"]
__version__ = "0.0.0"

with open("schema.json") as f:
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
        jsonschema.validate(self, typez_schema)


Definitions = Dict[str, Union[Kind, Function]]


@dataclass
class Kind:
    params: Optional[List[str]] = None


@dataclass
class Function:
    params: List[Tuple[str, Type]]
    return_: Type
    type_params: Optional[List[str]] = None


Type = Union[TypeParameter, DeclaredType, ExternalType]


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


Nodes = Dict[str, Union[CallNode, PrimitiveNode]]


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


TypeInstance = Union[DeclaredTypeInstance, ExternalTypeInstance]


@dataclass
class DeclaredTypeInstance:
    type: str
    params: Optional[List[TypeInstance]] = None


@dataclass
class ExternalTypeInstance:
    repr: str


States = List[State]


@dataclass
class State:
    node: str
    rule: str
    label: Optional[str] = None
