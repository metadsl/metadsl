import typing

import llvmlite.ir

from metadsl import *
from metadsl_core import *
from .pure import *


T = typing.TypeVar("T")
U = typing.TypeVar("U")
V = typing.TypeVar("V")
X = typing.TypeVar("X")


@expression
def module(name: str) -> llvmlite.ir.Module:
    return llvmlite.ir.Module(name)


@expression
def function_type(
    return_type: llvmlite.ir.Type, *args: llvmlite.ir.Type
) -> llvmlite.ir.FunctionType:
    return llvmlite.ir.FunctionType(return_type, args)


@expression
def function_decleration(
    module: llvmlite.ir.Module, type: llvmlite.ir.FunctionType, name: str
) -> llvmlite.ir.Function:
    return llvmlite.ir.Function(module, type, name=name)


@expression
def function_module(function: llvmlite.ir.Function) -> llvmlite.ir.Module:
    return function.module


@expression
def function_builder(function: llvmlite.ir.Function) -> llvmlite.ir.Module:
    return function.module


# @expression
# def module_to_llvmlite(mod: Module) -> llvmlite.ir.Module:
#     ...


# @rule
# def unbox_module(name: str) -> R[llvmlite.ir.Module]:
#     return module_to_llvmlite(Module.create(name)), lambda: llvmlite.ir.Module(name)


# @rule
# def unbox_module_function(name: str) -> R[llvmlite.ir.Module]:
#     return (
#         mod.register_function_one(fn).left(),
#         declare_function(unbox_module(mod), unbox_function_type(fn), function.name),
#     )


# def registered_fn_one_to_fn(mod: Module, name: str, abs: Abstraction[T, U]):

#     return mod.register_function_one(FunctionOne.create(name, abs))
