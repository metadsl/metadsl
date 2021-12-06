"""
Represent Python Bytecode instructions as a data structure.

We build a SSA CFG from the bytecode, which builds up the data stacks
"""


from __future__ import annotations
from dataclasses import dataclass, field
from tkinter import N
from typing import Iterable, List, Optional
from itertools import chain
import dis


def instructions_from_bytes(b: bytes) -> Iterable[InstructionData]:
    extended_arg = 0
    for i in range(0, len(b), 2):
        # TODO: Longer value bytes
        opcode = b[i]
        arg = b[i + 1] | extended_arg
        if opcode == dis.EXTENDED_ARG:
            extended_arg = arg << 8
        else:
            extended_arg = 0
            yield InstructionData(i, opcode, arg)


def instructions_to_bytes(instructions: Iterable[InstructionData]) -> bytes:
    return bytes(
        chain.from_iterable(instruction.bytes() for instruction in instructions)
    )


@dataclass
class InstructionData:
    # The bytes offset of the instruction
    offset: int
    opcode: int
    arg: int

    # The bytes offset of the jump target, if it does jump.
    jump_target_offset: Optional[int] = field(init=False)

    def __post_init__(self):
        self.jump_target_offset = (
            self.arg
            if self.opcode in dis.hasjabs
            else self.offset + self.arg + 2
            if self.opcode in dis.hasjrel
            else None
        )

    def bytes(self) -> Iterable[int]:
        n_units = instrsize(self.arg)
        # Duplicate semantics of write_op_arg
        # to produce the the right number of extended arguments
        # https://github.com/python/cpython/blob/b2e5794870eb4728ddfaafc0f79a40299576434f/Python/wordcode_helpers.h#L22-L44
        for i in range(n_units, 0, -1):
            yield self.opcode if i == 1 else dis.EXTENDED_ARG
            yield (self.arg >> (8 * (i - 1))) & 0xFF


def instrsize(arg: int) -> int:
    """
    Minimum number of code units necessary to encode instruction with
    EXTENDED_ARGs

    From https://github.com/python/cpython/blob/b2e5794870eb4728ddfaafc0f79a40299576434f/Python/wordcode_helpers.h#L11-L20
    """
    return 1 if arg <= 0xFF else 2 if arg <= 0xFFFF else 3 if arg <= 0xFFFFFF else 4


# @dataclass
# class ControlFlowGraph:
#     """
#     The control flow graph represents the different "blocks" of instructions
#     that Python moves between as it executes the control flow.

#     Every instruction that is jumped to starts a new control flow block.
#     Every jump and return instructions ends a control flow block.
#     """

#     # List of blocks, keyed by index
#     blocks: list[Block]

#     # Mapping of bytecode offset to the offset of the block
#     bytecode_to_block: dict[int, int]

#     @classmethod
#     def from_instructions(
#         cls, instructions: Iterable[InstructionData]
#     ) -> ControlFlowGraph:
#         # First compute a sorted list of all bytecode offsets which are jump targets
#         targets = sorted(
#             set(i.jump_target for i in instructions if i.jump_target is not None)
#         )
#         # Then, iterate through every instruction,
#         current_block = Block([])
#         blocks = [current_block]
#         bytecode_to_block = {0: 0}
#         for instruction in instructions:
#             block = blocks.get(instruction.offset)


# @dataclass
# class Block:
#     instructions: List[InstructionData]
#     # the block which this jumps to
#     jump: Optional[int] = field(default=None)
