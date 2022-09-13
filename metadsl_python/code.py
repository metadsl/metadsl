"""

"""

from __future__ import annotations

from dataclasses import dataclass
from types import CodeType
from typing import Optional

from code_data import CodeData, Function, TypeOfCode
from metadsl import Expression
from metadsl.expressions import expression
from metadsl_core import Abstraction, Either, Integer, Maybe, Pair
from metadsl_core.boolean import Boolean
from metadsl_core.function import FunctionTwo
from metadsl_core.vec import Vec
from metadsl_rewrite import R, register, rule

register_code = register[__name__]


class Code(Expression):
    """
    A python bytecode objects.

    1. List of instructions, each which deal with the stack
    2.

    """

    @expression
    @property
    def type(self) -> Maybe[FunctionCodeType]:
        ...

    # @expression
    # @classmethod
    # def create(
    #     cls,
    #     # Make this vec of state -> state?
    #     fn: Abstraction[State, State],
    #     filename: str,
    #     line_number: int,
    #     name: str,
    #     type: TypeOfCode,
    #     freevars: tuple[str, ...],
    #     future_annotations: bool,
    # ) -> Code:
    #     ...

    @expression
    @classmethod
    def from_code_data(cls, code_data: CodeData) -> Code:
        ...

    @classmethod
    def from_code(cls, code: CodeType) -> Code:
        return cls.from_code_data(CodeData.from_code(code))


class FunctionCodeType(Expression):
    @expression
    @classmethod
    def from_data(cls, code_data_function: Function) -> FunctionType:
        ...

    @expression
    @property
    def docstring() -> Maybe[str]:
        ...

    @expression
    @property
    def type(self) -> FunctionType:
        ...

    @expression
    @property
    def args(self) -> Args:
        ...


class Args(Expression):
    """
    The arguments of a function.

    >>> a = Args.create(
        positional_only=Vec.create("a"),
        positional_or_keyword=Vec.create("b"),
        var_positional=Maybe.just("c"),
        keyword_only=Vec.create("d"),
        var_keyword=Maybe.just("e"),
    )
    >>> execute(a.positional_only)
    Vec.create("a")
    >>> execute(a.positional_or_keyword)
    Vec.create("b")
    >>> execute(a.var_positional)
    Maybe.just("c")
    >>> execute(a.keyword_only)
    Vec.create("d")
    >>> execute(a.var_keyword)
    Maybe.just("e")
    """

    @expression
    @classmethod
    def create(
        cls,
        positional_only: Vec[str],
        positional_or_keyword: Vec[str],
        var_positional: Maybe[str],
        keyword_only: Vec[str],
        var_keyword: Maybe[str],
    ) -> Args:
        ...

    @expression
    @property
    def positional_only(self) -> Vec[str]:
        ...

    @expression
    @property
    def positional_or_keyword(self) -> Vec[str]:
        ...

    @expression
    @property
    def var_positional(self) -> Maybe[str]:
        ...

    @expression
    @property
    def keyword_only(self) -> Vec[str]:
        ...

    @expression
    @property
    def var_keyword(self) -> Maybe[str]:
        ...


@register_code
@rule
def args_rules(
    positional_only: Vec[str],
    positional_or_keyword: Vec[str],
    var_positional: Maybe[str],
    keyword_only: Vec[str],
    var_keyword: Maybe[str],
):
    a = Args.create(
        positional_only=positional_only,
        positional_or_keyword=positional_or_keyword,
        var_positional=var_positional,
        keyword_only=keyword_only,
        var_keyword=var_keyword,
    )
    yield a.positional_only, positional_only
    yield a.positional_or_keyword, positional_or_keyword
    yield a.var_positional, var_positional
    yield a.keyword_only, keyword_only
    yield a.var_keyword, var_keyword


class FunctionType(Expression):
    @expression
    @property
    @classmethod
    def generator(cls) -> FunctionType:
        ...

    @expression
    @property
    @classmethod
    def coroutine(cls) -> FunctionType:
        ...

    @expression
    @property
    @classmethod
    def async_generator(cls) -> FunctionType:
        ...

    @expression
    @property
    @classmethod
    def normal(cls) -> FunctionType:
        ...

    @expression
    @property
    def is_coro(self) -> Boolean:
        ...


@register_code
@rule
def _code_rules(code_data: CodeData, fn: Function):
    yield Code.from_code_data(code_data).type, lambda: Maybe.just(
        FunctionType.from_data(code_data.type)
    ) if code_data.type else Maybe[FunctionType].nothing()

    yield FunctionCodeType.from_data(fn).type, lambda: (
        FunctionType.generator
        if fn.type == "GENERATOR"
        else FunctionType.coroutine
        if fn.type == "COROUTINE"
        else FunctionType.async_generator
        if fn.type == "ASYNC_GENERATOR"
        else FunctionType.normal
    )
    yield FunctionType.generator.is_coro, Boolean.true
    yield FunctionType.coroutine.is_coro, Boolean.true
    yield FunctionType.async_generator.is_coro, Boolean.true
    yield FunctionType.normal.is_coro, Boolean.false


# Below here is old


# @expression
# @classmethod
# def create(
#     cls, stack: Vec[Object], code: FunctionTwo[State, Integer, State]
# ) -> State:
#     ...

# @expression
# def execute_instruction(self, instruction: Instruction) -> State:
#     ...

# TODO: Move jump here?


# class Instruction(Expression):
#     """
#     A bytecode instruction.
#     """

#     @expression
#     @classmethod
#     def pop_top(cls) -> Instruction:
#         ...

#     @expression
#     @classmethod
#     def jump(cls, target: int) -> Instruction:
#         ...


# @register_stack
# @rule
# def stack_instructions(stack: Vec[Object]) -> R[Pair[Vec[Object], Object]]:
#     yield (
#         State.create(stack).execute_instruction(Instruction.pop_top()),
#         State.create(stack.pop().left),
#     )
#     yield state.jump(target)


# @FunctionTwo.from_fn_recursive
# def some_state(
#     fn: FunctionTwo[State, Integer, State], state: State, block: Integer
# ) -> State:
#     return Vec[Abstraction[State, State]].create(
#         Abstraction[State, State].from_fn(
#             lambda state: state.execute_instruction(Instruction.jump(1))
#         ),
#         Abstraction[State, State].from_fn(
#             lambda state: state.execute_instruction(Instruction.pop_top())
#         ),
#     )[block](state)
