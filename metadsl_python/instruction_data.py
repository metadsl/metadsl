from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple
from itertools import chain


def instructions_from_bytes(b: bytes) -> Iterable[InstructionData]:
    for i in range(0, len(b), 2):
        yield InstructionData(b[i], b[i + 1])


def instructions_to_bytes(instructions: Iterable[InstructionData]) -> bytes:
    return bytes(
        chain.from_iterable(
            (instruction.opcode, instruction.value) for instruction in instructions
        )
    )


@dataclass
class InstructionData:
    opcode: int
    value: int

