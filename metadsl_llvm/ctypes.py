from __future__ import annotations
import typing
import ctypes


from metadsl import *
from metadsl_core import *

__all__ = ["ctypes_rules", "CType", "CFunctionType"]


ctypes_rules = RulesRepeatFold()
register_ctypes = ctypes_rules.append


class CType(Expression):
    @expression
    @classmethod
    def c_int(cls) -> CType:
        ...

    @expression
    @classmethod
    def box(cls, tp: typing.Any) -> CType:
        ...


@register_ctypes
@rule
def ctype_cint() -> R[CType]:
    return CType.c_int(), lambda: CType.box(ctypes.c_int)


class CFunctionType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: CType, *args: CType) -> CFunctionType:
        ...

    # Cannot represent type of C function
    @expression
    @classmethod
    def box(cls, tp: typing.Any) -> CFunctionType:
        ...

    @expression
    def __call__(self, ptr: int) -> typing.Callable:
        ...


@register_ctypes
@rule
def c_function_type_create_1(
    return_tp: typing.Any, arg1: typing.Any
) -> R[CFunctionType]:
    return (
        CFunctionType.create(CType.box(return_tp), CType.box(arg1)),
        lambda: CFunctionType.box(ctypes.CFUNCTYPE(return_tp, arg1)),
    )


@register_ctypes
@rule
def c_function_type_create_2(
    return_tp: typing.Any, arg1: typing.Any, arg2: typing.Any
) -> R[CFunctionType]:
    return (
        CFunctionType.create(CType.box(return_tp), CType.box(arg1), CType.box(arg2)),
        lambda: CFunctionType.box(ctypes.CFUNCTYPE(return_tp, arg1, arg2)),
    )


@register_ctypes
@rule
def cfunc_call(fntype: typing.Any, ptr: int) -> R[typing.Callable]:
    return CFunctionType.box(fntype)(ptr), lambda: fntype(ptr)
