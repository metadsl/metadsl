from __future__ import annotations

from dataclasses import dataclass, field
from types import CodeType
from typing import Tuple

from .control_flow_graph import ControlFlowGraph, bytes_to_cfg, cfg_to_bytes
from .line_table import (
    LineTable,
    from_line_table,
    to_line_table,
)
from .flags_data import FlagsData, to_flags_data, from_flags_data
from .dataclass_hide_default import DataclassHideDefault
import sys


@dataclass
class CodeData(DataclassHideDefault):
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
    argcount: int = field(default=0)

    # number of positional only arguments
    posonlyargcount: int = field(default=0)

    # number of keyword only arguments (not including ** arg)
    kwonlyargcount: int = field(default=0)

    # number of local variables
    nlocals: int = field(default=0)

    # virtual machine stack space required
    stacksize: int = field(default=1)

    # code flags
    flags_data: FlagsData = field(default_factory=set)

    # Bytecode instructions
    cfg: ControlFlowGraph = field(default_factory=ControlFlowGraph)

    # tuple of constants used in the bytecode
    # All code objects are recursively transformed to CodeData objects
    consts: Tuple[object, ...] = field(default=(None,))

    # tuple of names of local variables
    names: Tuple[str, ...] = field(default=tuple())

    # tuple of names of arguments and local variables
    varnames: Tuple[str, ...] = field(default=tuple())

    # name of file in which this code object was created
    filename: str = field(default="<string>")

    # name with which this code object was defined
    name: str = field(default="<module>")

    # number of first line in Python source code
    firstlineno: int = field(default=1)

    line_table: LineTable = field(default_factory=to_line_table)

    # tuple of names of free variables (referenced via a function’s closure)
    freevars: Tuple[str, ...] = field(default=tuple())
    # tuple of names of cell variables (referenced by containing scopes)
    cellvars: Tuple[str, ...] = field(default=tuple())

    @property
    def flags(self) -> int:
        return from_flags_data(self.flags_data)

    @property
    def code(self) -> bytes:
        return cfg_to_bytes(self.cfg)

    @property
    def line_table_bytes(self) -> bytes:
        return from_line_table(self.line_table)

    def verify(self) -> None:
        self.cfg.verify()

    @classmethod
    def from_code(cls, code: CodeType) -> CodeData:
        if sys.version_info >= (3, 8):
            posonlyargcount = code.co_posonlyargcount
        else:
            posonlyargcount = 0

        if sys.version_info >= (3, 10):
            line_table = to_line_table(code.co_linetable)  # type: ignore
        else:
            line_table = to_line_table(code.co_lnotab)
        return cls(
            code.co_argcount,
            posonlyargcount,
            code.co_kwonlyargcount,
            code.co_nlocals,
            code.co_stacksize,
            to_flags_data(code.co_flags),
            bytes_to_cfg(code.co_code),
            tuple(map(to_code_constant, code.co_consts)),
            code.co_names,
            code.co_varnames,
            code.co_filename,
            code.co_name,
            code.co_firstlineno,
            line_table,
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
                self.line_table_bytes,
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
                self.line_table_bytes,
                self.freevars,
                self.cellvars,
            )


def to_code_constant(value: object) -> object:
    if isinstance(value, CodeType):
        return CodeData.from_code(value)
    return value


def from_code_constant(value: object) -> object:
    if isinstance(value, CodeData):
        return value.to_code()
    return value
