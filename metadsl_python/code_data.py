from __future__ import annotations

from dataclasses import dataclass
from types import CodeType
from typing import Tuple, List
from .code_flags_data import CodeFlagsData
from .instruction_data import (
    InstructionData,
    instructions_from_bytes,
    instructions_to_bytes,
)


# TODO: Should this just be the data description?
# Then another class for flags... and another for bytecode...?
# Is there a better way to do this iteratively?


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
    flags: CodeFlagsData

    # Bytecode instructions
    instructions: List[InstructionData]

    # tuple of constants used in the bytecode
    consts: Tuple[object, ...]

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

    # encoded mapping of line numbers to bytecode indices
    # TODO: Decode this
    lnotab: bytes

    # tuple of names of free variables (referenced via a function’s closure)
    freevars: Tuple[str, ...]
    # tuple of names of cell variables (referenced by containing scopes)
    cellvars: Tuple[str, ...]

    @classmethod
    def from_code(cls, code: CodeType) -> CodeData:
        return cls(
            code.co_argcount,
            code.co_posonlyargcount,
            code.co_kwonlyargcount,
            code.co_nlocals,
            code.co_stacksize,
            CodeFlagsData.from_flags(code.co_flags),
            list(instructions_from_bytes(code.co_code)),
            code.co_consts,
            code.co_names,
            code.co_varnames,
            code.co_filename,
            code.co_name,
            code.co_firstlineno,
            code.co_lnotab,
            code.co_freevars,
            code.co_cellvars,
        )

    def to_code(self) -> CodeType:
        # https://github.com/python/cpython/blob/cd74e66a8c420be675fd2fbf3fe708ac02ee9f21/Lib/test/test_code.py#L217-L232
        return CodeType(
            self.argcount,
            self.posonlyargcount,
            self.kwonlyargcount,
            self.nlocals,
            self.stacksize,
            self.flags.to_flags(),
            instructions_to_bytes(self.instructions),
            self.consts,
            self.names,
            self.varnames,
            self.filename,
            self.name,
            self.firstlineno,
            self.lnotab,
            self.freevars,
            self.cellvars,
        )
