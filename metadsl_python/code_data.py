"""
Wrapper around code_data types, so that we can mach against them.

All types are prefixed with `M` to differentiate between the wrapped versions in a
concise way.
"""

from __future__ import annotations

from types import CodeType
from typing import Optional, Sequence, TypeVar

from code_data import (
    Arg,
    Args,
    Cellvar,
    CodeData,
    Constant,
    Freevar,
    FunctionType,
    Instruction,
    Jump,
    Name,
    NoArg,
    TypeOfCode,
    Varname,
)

from metadsl import Expression
from metadsl_core import Integer, Maybe
from metadsl_core.vec import Vec
from metadsl_rewrite import datatype_rule, default_rule, enum_rule, register


class MCodeData(Expression, wrap_methods=True):
    """
    A python bytecode objects.

    >>> from metadsl_rewrite import execute
    >>> execute(MCodeData.from_code(compile("x[y]", "<string>", "eval")))
    marg_0 = MArg.none()
    MCodeData.create(
        MBlocks.create(
            Vec.create(
                Vec.create(
                    MInstruction.create("LOAD_NAME", MArg.name("x"), 1),
                    MInstruction.create("LOAD_NAME", MArg.name("y"), 1),
                    MInstruction.create("BINARY_SUBSCR", marg_0, 1),
                    MInstruction.create("RETURN_VALUE", marg_0, 1),
                )
            )
        ),
        "<string>",
        1,
        "<module>",
        2,
        MTypeOfCode.none(),
        Vec.create(),
        True,
    )
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
    ) -> MCodeData:
        ...

    def update(
        self,
        blocks: MBlocks = ...,
        filename: str = ...,
        first_line_number: int = ...,
        name: str = ...,
        stacksize: int = ...,
        type: MTypeOfCode = ...,
        freevars: Vec[str] = ...,
        future_annotations: bool = ...,
    ) -> MCodeData:
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

    @classmethod
    def from_code_data(cls, code_data: CodeData) -> MCodeData:
        return MCodeData.create(
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
    def from_code(cls, code: CodeType) -> MCodeData:
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

    # The type of constant should be ConstantValue, but get_type_hints doesn't
    # support recursive types yet
    @classmethod
    def constant(cls, constant: object) -> MArg:
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
            Maybe[str].from_optional(type_of_code.docstring),
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
    """
    The type of a function.

    >>> from metadsl_rewrite import execute
    >>> execute(MFunctionType.generator().match(1, 2, 3, 4))
    1
    """

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


register_code(datatype_rule(MCodeData))
register_code(default_rule(MCodeData.from_code))
register_code(default_rule(MCodeData.from_code_data))

register_code(default_rule(MBlocks.from_blocks))

register_code(default_rule(MInstruction.from_instruction))

register_code(default_rule(MArg.from_arg))

register_code(datatype_rule(MTypeOfCode))
register_code(default_rule(MTypeOfCode.from_type_of_code))

register_code(datatype_rule(MArgs))
register_code(default_rule(MArgs.from_args))


register_code(enum_rule(MFunctionType))
