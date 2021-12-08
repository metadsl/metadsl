from __future__ import annotations
from ast import Constant

from dataclasses import dataclass
from types import CodeType
from typing import FrozenSet, Tuple, List, Union
from .code_flags_data import CodeFlagsData
from .instruction_data import (
    InstructionData,
    instructions_from_bytes,
    instructions_to_bytes,
)
import sys


@dataclass
class CodeData:
    """
    A code object is what is seralized on disk as PYC file. It is the lowest
    abstraction level CPython provides before execution.

    This class is meant to a be a data description of a code object,
    where the types of the attributes can help us understand what the different
    possible options are.

    All recursive code object are translated to code data as well.

    From https://docs.python.org/3/library/inspect.html
    """

    # number of arguments (not including keyword only arguments, * or ** args)
    argcount: int

    # number of positional only arguments
    posonlyargcount: int

    # number of keyword only arguments (not including ** arg)
    kwonlyargcount: int

    # number of local variables
    nlocals: int

    # virtual machine stack space required
    stacksize: int

    # code flags
    flags_data: CodeFlagsData

    # Bytecode instructions
    instructions: List[InstructionData]

    # tuple of constants used in the bytecode
    consts: Tuple[CodeConstant, ...]

    # tuple of names of local variables
    names: Tuple[str, ...]

    # tuple of names of arguments and local variables
    varnames: Tuple[str, ...]

    # name of file in which this code object was created
    filename: str

    # name with which this code object was defined
    name: str

    # number of first line in Python source code
    firstlineno: int

    line_mapping: BytecodeLineMapping

    # tuple of names of free variables (referenced via a function’s closure)
    freevars: Tuple[str, ...]
    # tuple of names of cell variables (referenced by containing scopes)
    cellvars: Tuple[str, ...]

    @property
    def flags(self) -> int:
        return self.flags_data.to_flags()

    @property
    def code(self) -> bytes:
        return instructions_to_bytes(self.instructions)

    @classmethod
    def from_code(cls, code: CodeType) -> CodeData:
        if sys.version_info >= (3, 8):
            posonlyargcount = code.co_posonlyargcount
        else:
            posonlyargcount = 0

        if sys.version_info >= (3, 10):
            line_mapping = LineTable(code.co_linetable)
        else:
            line_mapping = LineMapping(code.co_lnotab)
        return cls(
            code.co_argcount,
            posonlyargcount,
            code.co_kwonlyargcount,
            code.co_nlocals,
            code.co_stacksize,
            CodeFlagsData.from_flags(code.co_flags),
            list(instructions_from_bytes(code.co_code)),
            tuple(map(to_code_constant, code.co_consts)),
            code.co_names,
            code.co_varnames,
            code.co_filename,
            code.co_name,
            code.co_firstlineno,
            line_mapping,
            code.co_freevars,
            code.co_cellvars,
        )

    def to_code(self) -> CodeType:
        consts = tuple(map(from_code_constant, self.consts))
        # https://github.com/python/cpython/blob/cd74e66a8c420be675fd2fbf3fe708ac02ee9f21/Lib/test/test_code.py#L217-L232
        if sys.version_info >= (3, 8):
            return CodeType(
                self.argcount,
                # Only include this on 3.8+
                self.posonlyargcount,
                self.kwonlyargcount,
                self.nlocals,
                self.stacksize,
                self.flags,
                self.code,
                consts,
                self.names,
                self.varnames,
                self.filename,
                self.name,
                self.firstlineno,
                self.line_mapping.bytes,
                self.freevars,
                self.cellvars,
            )
        else:
            return CodeType(
                self.argcount,
                self.kwonlyargcount,
                self.nlocals,
                self.stacksize,
                self.flags,
                self.code,
                consts,
                self.names,
                self.varnames,
                self.filename,
                self.name,
                self.firstlineno,
                self.line_mapping.bytes,
                self.freevars,
                self.cellvars,
            )


@dataclass
class LineTable:
    """
    PEP 626 line number table.
    """

    bytes: bytes


@dataclass
class LineMapping:
    """
    Pre PEP 626 line number mapping
    """

    bytes: bytes


BytecodeLineMapping = Union[LineMapping, LineTable]


@dataclass
class ConstanValue:
    value: object


CodeConstant = Union[ConstanValue, CodeData]


def to_code_constant(value: object) -> CodeConstant:
    if isinstance(value, CodeType):
        return CodeData.from_code(value)
    return ConstanValue(value)


def from_code_constant(value: CodeConstant) -> object:
    if isinstance(value, ConstanValue):
        return value.value
    return value.to_code()
