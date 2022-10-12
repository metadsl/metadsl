"""
Wrapper around code_data types, so that we can mach against them.

All types are prefixed with `M` to differentiate between the wrapped versions in a
concise way.
"""

from __future__ import annotations

from types import CodeType
from typing import Optional, Sequence, TypeVar

from code_data import (Arg, Args, Cellvar, CodeData, Constant, ConstantValue,
                       Freevar, FunctionType, Instruction, Jump, Name, NoArg,
                       TypeOfCode, Varname)
from metadsl import Expression
from metadsl_core import Integer, Maybe
from metadsl_core.vec import Vec
from metadsl_rewrite import datatype_rule, register, rule
from metadsl_rewrite.rules import default_rule


class MCode(Expression, wrap_methods=True):
    """
    A python bytecode objects.

    >>> from metadsl_rewrite import execute
    >>> def fn(a: int):
    ...     return a * 2
    >>> execute(MCode.from_code(fn.__code__))
    """

    @classmethod
    def create(
        cls,
        blocks: MBlocks,
        filename: str,
        first_line_number: int,
        name: str,
        stacksize: int,
        type: MTypeOfCode,
        freevars: Vec[str],
        future_annotations: bool,
    ) -> MCode:
        ...

    @property
    def blocks(self) -> MBlocks:
        ...

    @property
    def filename(self) -> str:
        ...

    @property
    def first_line_number(self) -> int:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def stacksize(self) -> int:
        ...

    @property
    def type(self) -> MTypeOfCode:
        ...

    @property
    def freevars(self) -> Vec[str]:
        ...

    @property
    def future_annotations(self) -> bool:
        ...

    def set_blocks(self, blocks: MBlocks) -> MCode:
        ...

    def set_filename(self, filename: str) -> MCode:
        ...

    def set_first_line_number(self, first_line_number: int) -> MCode:
        ...

    def set_name(self, name: str) -> MCode:
        ...

    def set_stacksize(self, stacksize: int) -> MCode:
        ...

    def set_type(self, type: MTypeOfCode) -> MCode:
        ...

    def set_freevars(self, freevars: Vec[str]) -> MCode:
        ...

    def set_future_annotations(self, future_annotations: bool) -> MCode:
        ...

    @classmethod
    def from_code_data(cls, code_data: CodeData) -> MCode:
        return MCode.create(
            MBlocks.from_blocks(code_data.blocks),
            code_data.filename,
            code_data.first_line_number,
            code_data.name,
            code_data.stacksize,
            MTypeOfCode.from_type_of_code(code_data.type),
            Vec.create(*code_data.freevars),
            code_data.future_annotations,
        )

    @classmethod
    def from_code(cls, code: CodeType) -> MCode:
        return cls.from_code_data(CodeData.from_code(code))


class MBlocks(Expression, wrap_methods=True):
    """
    A list of blocks
    """

    @classmethod
    def create(cls, blocks: Vec[Vec[MInstruction]]) -> MBlocks:
        ...

    @classmethod
    def from_blocks(cls, blocks: Sequence[Sequence[Instruction]]) -> MBlocks:
        return MBlocks.create(
            Vec.create(
                *(
                    Vec.create(*(MInstruction.from_instruction(i) for i in b))
                    for b in blocks
                )
            )
        )


class MInstruction(Expression, wrap_methods=True):
    """
    A single instruction
    """

    @classmethod
    def create(cls, name: str, arg: MArg, line_number: Optional[int]) -> MInstruction:
        ...

    @classmethod
    def from_instruction(cls, instruction: Instruction) -> MInstruction:
        return MInstruction.create(
            instruction.name,
            MArg.from_arg(instruction.arg),
            instruction.line_number,
        )


class MArg(Expression, wrap_methods=True):
    @classmethod
    def int(cls, value: int) -> MArg:
        ...

    @classmethod
    def jump(cls, target: Integer) -> MArg:
        ...

    @classmethod
    def name(cls, name: str) -> MArg:
        ...

    @classmethod
    def varname(cls, varname: str) -> MArg:
        ...

    @classmethod
    def constant(cls, constant: ConstantValue) -> MArg:
        ...

    @classmethod
    def freevar(cls, freevar: str) -> MArg:
        ...

    @classmethod
    def cellvar(cls, cellvar: str) -> MArg:
        ...

    @classmethod
    def none(cls) -> MArg:
        ...

    @classmethod
    def from_arg(cls, arg: Arg) -> MArg:
        if isinstance(arg, int):
            return MArg.int(arg)
        if isinstance(arg, Jump):
            return MArg.jump(Integer.from_int(arg.target))
        if isinstance(arg, Name):
            return MArg.name(arg.name)
        if isinstance(arg, Varname):
            return MArg.varname(arg.varname)
        if isinstance(arg, Constant):
            return MArg.constant(arg.constant)
        if isinstance(arg, Freevar):
            return MArg.freevar(arg.freevar)
        if isinstance(arg, Cellvar):
            return MArg.cellvar(arg.cellvar)
        assert isinstance(arg, NoArg)
        return MArg.none()


class MTypeOfCode(Expression, wrap_methods=True):
    @classmethod
    def none(cls) -> MTypeOfCode:
        ...

    @classmethod
    def create(
        cls,
        args_: MArgs,
        docstring: Maybe[str],
        type: MFunctionType,
    ) -> MTypeOfCode:
        ...

    @property
    def docstring(self) -> Maybe[str]:
        ...

    @property
    def type(self) -> MFunctionType:
        ...

    @property
    def args_(self) -> MArgs:
        ...

    @classmethod
    def from_type_of_code(cls, type_of_code: TypeOfCode) -> MTypeOfCode:
        if type_of_code is None:
            return MTypeOfCode.none()
        return cls.create(
            MArgs.from_args(type_of_code.args),
            Maybe.from_optional(type_of_code.docstring),
            MFunctionType.from_function_type(type_of_code.type),
        )


class MArgs(Expression, wrap_methods=True):
    """
    The arguments of a function.
    """

    @classmethod
    def create(
        cls,
        positional_only: Vec[str],
        positional_or_keyword: Vec[str],
        var_positional: Maybe[str],
        keyword_only: Vec[str],
        var_keyword: Maybe[str],
    ) -> MArgs:
        ...

    @property
    def positional_only(self) -> Vec[str]:
        ...

    @property
    def positional_or_keyword(self) -> Vec[str]:
        ...

    @property
    def var_positional(self) -> Maybe[str]:
        ...

    @property
    def keyword_only(self) -> Vec[str]:
        ...

    @property
    def var_keyword(self) -> Maybe[str]:
        ...

    @classmethod
    def from_args(cls, args: Args) -> MArgs:
        return cls.create(
            Vec.create(*args.positional_only),
            Vec.create(*args.positional_or_keyword),
            Maybe.from_optional(args.var_positional),
            Vec.create(*args.keyword_only),
            Maybe.from_optional(args.var_keyword),
        )


class MFunctionType(Expression, wrap_methods=True):
    @classmethod
    def generator(cls) -> MFunctionType:
        ...

    @classmethod
    def coroutine(cls) -> MFunctionType:
        ...

    @classmethod
    def async_generator(cls) -> MFunctionType:
        ...

    @classmethod
    def normal(cls) -> MFunctionType:
        ...

    # TODO: Maybe make enum creator class like the dataclass creator rules,
    # to use for this and either
    def match(self, generator: T, coroutine: T, async_generator: T, normal: T) -> T:
        ...

    @classmethod
    def from_function_type(cls, function_type: FunctionType) -> MFunctionType:
        if function_type == "GENERATOR":
            return MFunctionType.generator()
        if function_type == "COROUTINE":
            return MFunctionType.coroutine()
        if function_type == "ASYNC_GENERATOR":
            return MFunctionType.async_generator()
        assert function_type is None
        return MFunctionType.normal()



T = TypeVar("T")

register_code = register[__name__]


register_code(datatype_rule(MCode))
register_code(default_rule(MCode.from_code))
register_code(default_rule(MCode.from_code_data))

register_code(default_rule(MBlocks.from_blocks))

register_code(default_rule(MInstruction.from_instruction))

register_code(default_rule(MArg.from_arg))

register_code(datatype_rule(MTypeOfCode))
register_code(default_rule(MTypeOfCode.from_type_of_code))

register_code(datatype_rule(MArgs))
register_code(default_rule(MArgs.from_args))


@register_code
@rule
def _m_function_type_match(generator: T, coroutine: T, async_generator: T, normal: T):
    yield MFunctionType.generator().match(
        generator, coroutine, async_generator, normal
    ), generator
    yield MFunctionType.coroutine().match(
        generator, coroutine, async_generator, normal
    ), coroutine
    yield MFunctionType.async_generator().match(
        generator, coroutine, async_generator, normal
    ), async_generator
    yield MFunctionType.normal().match(
        generator, coroutine, async_generator, normal
    ), normal
