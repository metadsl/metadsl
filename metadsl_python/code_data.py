from __future__ import annotations

from types import CodeType

from metadsl import Expression
from metadsl_core import Abstraction, Either, Maybe

from code_data import CodeData, TypeOfCode


class State(Expression):
    """
    State is a data type that represents a state of the program and external state.
    """

    ...


class Code(Expression):
    """
    A python bytecode objects.
    """

    @classmethod
    def create(
        cls,
        fn: Abstraction[State, State],
        filename: str,
        line_number: int,
        name: str,
        type: TypeOfCode,
        freevars: tuple[str, ...],
        future_annotations: bool,
    ) -> Code:
        ...

    @classmethod
    def from_code_data(cls, code_data: CodeData) -> Code:
        ...

    @classmethod
    def from_code(cls, code: CodeType) -> Code:
        ...
