from __future__ import annotations

from metadsl import *
from metadsl_core import *


class Module(Expression):
    """
    https://llvmlite.readthedocs.io/en/latest/glossary.html#module
    """

    @expression
    @classmethod
    def create(cls, *functions: Function) -> Module:
        ...


class Function(Expression):
    @expression
    @classmethod
    def create(cls, name: str, typ: FunctionType, *blocks: BasicBlock) -> Function:
        ...


class BasicBlock(Expression):
    @expression
    @classmethod
    def create(cls, label: str, *instructions: Instruction) -> BasicBlock:
        ...


class Instruction(Expression):
    pass


class FunctionType(Expression):
    @expression
    @classmethod
    def create(cls, return_type: Type, var_arg: bool, *args: Type) -> FunctionType:
        ...


class Type(Expression):
    @expression
    @classmethod
    def pointer(cls, pointee: Type, addrspace: int = 0) -> Type:
        ...

    @expression
    @classmethod
    def int_(cls, width: int) -> Type:
        ...

    @expression
    @classmethod
    def float_(cls) -> Type:
        ...

    @expression
    @classmethod
    def double(cls) -> Type:
        ...

    @expression
    @classmethod
    def void(cls) -> Type:
        ...

    @expression
    @classmethod
    def array(cls, element: Type, count: int) -> Type:
        ...

    @expression
    @classmethod
    def vector(cls, element: Type, count: int) -> Type:
        ...

    @expression
    @classmethod
    def elements(cls, *elements: Type, packed: int = False) -> Type:
        ...
