"""
Generate LLVM IR
"""

from __future__ import annotations
import typing

import llvmlite.ir as ir

from metadsl import *
from metadsl_core import *


__all__ = [
    "ModRef",
    "FnRef",
    "Type",
    "FnType",
    "BlockRef",
    "Value",
    "Terminate",
    "Fn",
    "Mod",
    "_Uniq",
]


class Mod(Expression):
    @expression  # type: ignore
    @property
    def functions(self) -> Vec[Fn]:
        ...

    @expression  # type: ignore
    @property
    def ref(self) -> ModRef:
        ...


class Fn(Expression):
    @expression  # type: ignore
    @property
    def blocks(self) -> Vec[Terminate]:
        ...

    @expression  # type: ignore
    @property
    def ref(self) -> FnRef:
        ...


class Terminate(Expression):
    """
    Returned at the end of a block.
    """

    pass


class Value(Expression):
    @expression
    @classmethod
    def constant(cls, type: Type, value: typing.Any) -> Value:
        ...


class BlockRef(Expression):
    @expression
    def ret(self, value: Value) -> Terminate:
        ...

    @expression
    def icmp_signed(self, operator: str, left: Value, right: Value) -> Value:
        ...

    @expression
    def call(self, function: FnRef, args: Vec[Value]) -> Value:
        ...

    @expression
    def cbranch(self, condition: Value, true: BlockRef, false: BlockRef) -> Terminate:
        ...

    @expression
    def add(self, left: Value, right: Value) -> Value:
        ...

    @expression
    def sub(self, left: Value, right: Value) -> Value:
        ...


class _Uniq:
    """
    Unique value that should only be equal to itself.

    Used so that multiple blocks can each be created with a different
    object so they will not be combined.
    """

    def __eq__(self, value) -> bool:
        return self is value

    def __str__(self) -> str:
        return str(id(self))

    def __repr__(self) -> str:
        return f"#{self}"


class FnRef(Expression):
    @expression
    def fn(self, blocks: Vec[Terminate]) -> Fn:
        ...

    def block(self, is_first: bool, name: typing.Union[str, None] = None) -> BlockRef:
        return self._block(is_first, name, _Uniq())

    @expression
    def _block(
        self, is_first: bool, name: typing.Union[str, None], uniq: _Uniq
    ) -> BlockRef:
        ...

    @expression  # type: ignore
    @property
    def arguments(self) -> Vec[Value]:
        ...

    @expression  # type: ignore
    @property
    def name(self) -> str:
        ...

    @expression  # type: ignore
    @property
    def type(self) -> FnType:
        ...


class ModRef(Expression):
    @expression
    @classmethod
    def create(cls, name: str) -> ModRef:
        ...

    @expression
    def fn(self, name: str, type: FnType, calling_convention: str = "") -> FnRef:
        ...

    @expression
    def mod(self, functions: Vec[Fn]) -> Mod:
        ...


class FnType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: Type, *arg_types: Type) -> FnType:
        ...


class Type(Expression):
    @expression
    @classmethod
    def create_int(cls, bits: int) -> Type:
        ...


@register
@rule
def mod_functions(ref: ModRef, fns: Vec[Fn]):
    return (ref.mod(fns).functions, fns)


@register
@rule
def mod_ref(ref: ModRef, fns: Vec[Fn]):
    return (ref.mod(fns).ref, ref)


@register
@rule
def fn_blocks(ref: FnRef, blocks: Vec[Terminate]):
    return (ref.fn(blocks).blocks, blocks)


@register
@rule
def fn_ref(ref: FnRef, blocks: Vec[Terminate]):
    return (ref.fn(blocks).ref, ref)


@register
@rule
def fn_ref_get_name(mod: ModRef, name: str, tp: FnType, calling_convention: str):
    return mod.fn(name, tp, calling_convention).name, name


@register
@rule
def fn_ref_get_type(mod: ModRef, name: str, tp: FnType, calling_convention: str):
    return mod.fn(name, tp, calling_convention).type, tp
