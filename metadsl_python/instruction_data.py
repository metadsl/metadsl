from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Protocol, Callable
from itertools import chain
from functools import partial
from abc import abstractmethod


def instructions_from_bytes(b: bytes) -> Iterable[InstructionData]:
    for i in range(0, len(b), 2):
        bytecode = b[i]
        value = b[i + 1]
        yield instruction_creators[bytecode](value)


def instructions_to_bytes(instructions: Iterable[InstructionData]) -> bytes:
    return bytes(
        chain.from_iterable(
            (instruction.opcode, instruction.value) for instruction in instructions
        )
    )


class InstructionData(Protocol):
    opcode: int
    value: int


@dataclass
class UnknownInstruction:
    opcode: int
    value: int


# List indexed by btecode, to make instruction data from the value
instruction_creators: List[Callable[[int], InstructionData]] = [
    partial(UnknownInstruction, op) for op in range(256)
]


class RegisterOpcode(InstructionData):
    def __init_subclass__(cls) -> None:
        if hasattr(cls, "opcode"):
            instruction_creators[cls.opcode] = cls.from_value

    @classmethod
    @abstractmethod
    def from_value(cls, value: int) -> InstructionData:
        ...


@dataclass  # type: ignore
class NoValue(RegisterOpcode):
    value: int

    @classmethod
    def from_value(cls, value: int) -> NoValue:
        return cls(value)


@dataclass
class Nop(NoValue):
    """
    Do nothing code. Used as a placeholder by the bytecode optimizer.
    """

    opcode = 9
