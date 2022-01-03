"""
Represent Python Bytecode instructions as a data structure.

"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Optional
from itertools import chain
import dis


def instructions_from_bytes(b: bytes) -> Iterable[InstructionData]:
    extended_arg = 0
    n_extended_args = 0
    for i in range(0, len(b), 2):
        # TODO: Longer value bytes
        opcode = b[i]
        arg = b[i + 1] | extended_arg
        if opcode == dis.EXTENDED_ARG:
            extended_arg = arg << 8
            n_extended_args += 1
        else:
            extended_arg = 0
            yield InstructionData(i, n_extended_args, opcode, arg)
            n_extended_args = 0


def instructions_to_bytes(instructions: Iterable[InstructionData]) -> bytes:
    return bytes(
        chain.from_iterable(instruction.bytes() for instruction in instructions)
    )


@dataclass
class InstructionData:
    # TODO: Don't store offset or jump target offeset, instead store block number
    # The bytes offset of the instruction
    offset: int
    # The number of extended args
    # Note: in Python >= 3.10 we can calculute this from the instruction size,
    # using `instrsize`, but in python < 3.10, sometimes instructions are prefixed
    # with extended args with value 0 (not sure why or how), so we need to save
    # the value manually to recreate the instructions
    n_extended_args: int = field(repr=False)

    opcode: int
    arg: int

    # The bytes offset of the jump target, if it does jump.
    jump_target_offset: Optional[int] = field(init=False)

    name: str = field(init=False)

    def __post_init__(self):
        # The total numver of required args should be at least big enough to hold the arg
        assert self.n_extended_args + 1 >= instrsize(self.arg)

        # Copied from dis.findlabels
        self.jump_target_offset = (
            self.arg
            if self.opcode in dis.hasjabs
            else self.offset + 2 + self.arg
            if self.opcode in dis.hasjrel
            else None
        )

        self.name = dis.opname[self.opcode]

    def bytes(self) -> Iterable[int]:
        # Duplicate semantics of write_op_arg
        # to produce the the right number of extended arguments
        # https://github.com/python/cpython/blob/b2e5794870eb4728ddfaafc0f79a40299576434f/Python/wordcode_helpers.h#L22-L44
        for i in range(self.n_extended_args, -1, -1):
            yield self.opcode if i == 0 else dis.EXTENDED_ARG
            yield (self.arg >> (8 * i)) & 0xFF

    def offsets(self) -> Iterable[int]:
        """
        Returns all the offsets for the instruction, including those for the extended
        args that appear before it
        """
        yield self.offset
        for i in range(self.n_extended_args):
            yield self.offset - (i * 2)


def instrsize(arg: int) -> int:
    """
    Minimum number of code units necessary to encode instruction with
    EXTENDED_ARGs

    From https://github.com/python/cpython/blob/b2e5794870eb4728ddfaafc0f79a40299576434f/Python/wordcode_helpers.h#L11-L20
    """
    return 1 if arg <= 0xFF else 2 if arg <= 0xFFFF else 3 if arg <= 0xFFFFFF else 4
