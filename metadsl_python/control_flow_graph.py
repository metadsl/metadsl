"""
Decodes the linear list of instructions into a control flow graph.

This representation is a list blocks, where each block is a list of instructions.

Every instruction that is jumped to starts a new control flow block.
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Optional, Union, List

from .dataclass_hide_default import DataclassHideDefault
import dis
from .instruction_data import (
    instrsize,
    instructions_from_bytes,
    InstructionData,
)


def bytes_to_cfg(b: bytes) -> ControlFlowGraph:
    instructions = list(instructions_from_bytes(b))

    # First compute a sorted list of all bytecode offsets which are jump targets
    # plus the initial offset of 0
    # This is to know which block each offset belongs to
    targets = sorted(
        set(
            i.jump_target_offset
            for i in instructions
            if i.jump_target_offset is not None
        )
        | {0}
    )
    block: list[Instruction] = []
    blocks: ControlFlowGraph = []
    for instruction_data in instructions:
        # If any of this instructions offsets are a jump target, start a new block
        # TODO: Just try first offset?
        for offset in instruction_data.offsets():
            if offset in targets:
                block = []
                blocks.append(block)
                break
        # Create an instruction for this instruction data
        arg: Arg
        if instruction_data.jump_target_offset is None:
            arg = instruction_data.arg
        else:
            arg = Jump(
                targets.index(instruction_data.jump_target_offset),
                relative=instruction_data.opcode() in dis.hasjrel,
            )

        instruction = Instruction(
            instruction_data.name,
            arg,
            instruction_data.n_args_override,
        )
        block.append(instruction)

    return blocks


def cfg_to_bytes(cfg: ControlFlowGraph) -> bytes:
    # First compute mapping from block to offset
    changed_instruction_lengths = True
    # So that we know the bytecode offsets for jumps when iterating though instructions
    block_index_to_instruction_offset: dict[int, int] = {}

    # Mapping of block index, instruction index, to integer arg values
    args: dict[tuple[int, int], int] = {}
    while changed_instruction_lengths:

        current_instruction_offset = 0
        # First go through and update all the instruction blocks
        for block_index, block in enumerate(cfg):
            block_index_to_instruction_offset[block_index] = current_instruction_offset
            for instruction_index, instruction in enumerate(block):
                if (block_index, instruction_index) in args:
                    arg_value = args[block_index, instruction_index]
                else:
                    arg = instruction.arg
                    if isinstance(arg, Jump):
                        # Otherwise use `1` as the arg_value, which will be updated later
                        arg_value = 1
                    else:
                        arg_value = arg
                    args[block_index, instruction_index] = arg_value
                n_instructions = instruction.n_args_override or instrsize(arg_value)
                current_instruction_offset += n_instructions
        # Then go and update all the jump instructions. If any of them
        # change the number of instructions needed for the arg, repeat
        changed_instruction_lengths = False
        current_instruction_offset = 0
        for block_index, block in enumerate(cfg):
            for instruction_index, instruction in enumerate(block):
                arg = instruction.arg
                if isinstance(arg, Jump):
                    target_instruction_offset = block_index_to_instruction_offset[
                        arg.target
                    ]
                    if arg.relative:
                        arg_value = (
                            target_instruction_offset - current_instruction_offset - 1
                        ) * (1 if ATLEAST_310 else 2)
                    else:
                        arg_value = (
                            1 if ATLEAST_310 else 2
                        ) * target_instruction_offset
                    if not instruction.n_args_override and instrsize(
                        args[block_index, instruction_index]
                    ) != instrsize(arg_value):
                        changed_instruction_lengths = True
                    args[block_index, instruction_index] = arg_value
                else:
                    arg_value = args[block_index, instruction_index]
                n_instructions = instruction.n_args_override or instrsize(arg_value)
                current_instruction_offset += n_instructions
    bytes_ = b""
    for block_index, block in enumerate(cfg):
        for instruction_index, instruction in enumerate(block):
            instruction_data = InstructionData(
                None,  # type: ignore
                instruction.name,
                args[block_index, instruction_index],
                instruction.n_args_override,
            )
            bytes_ += bytes(instruction_data.bytes())
    return bytes_


# How does python compute the byte offsets when jumping if the number of bytes
# in the jump can influence the offset?
# Where does it do this?
# Does it keep looping until its stable?


def verify_cfg(cfg: ControlFlowGraph) -> None:
    """
    Verify that the control flow graph is valid, by making sure every
    instruction that jumps can find it's block.
    """
    for block in cfg:
        assert block, "Block is empty"
        for instruction in block:
            arg = instruction.arg
            if isinstance(arg, Jump):
                assert arg.target in range(len(cfg)), "Jump target is out of range"


@dataclass
class Instruction(DataclassHideDefault):

    # The name of the instruction
    name: str

    # The integer value of the arg
    arg: Arg

    # The number of args, if it differs form the instrsize
    # Note: in Python >= 3.10 we can calculute this from the instruction size,
    # using `instrsize`, but in python < 3.10, sometimes instructions are prefixed
    # with extended args with value 0 (not sure why or how), so we need to save
    # the value manually to recreate the instructions
    n_args_override: Optional[int] = field(repr=False, default=1)

    # TODO: Add value for compilation out


@dataclass
class Jump:
    # The block index of the target
    target: int
    # Whether the jump is absolute or relative
    relative: bool = field(repr=False)


# TODO: Add:
# 1. constant lookup
# 2. a name lookup
# 3. a local lookup
# 5. An unused value
# 6. Comparison lookup
# 7. format value
# 8. Generator kind

Arg = Union[int, Jump]
ControlFlowGraph = List[List[Instruction]]

# Bytecode instructions jumps refer to the instruction offset, instead of byte
# offset in Python >= 3.10 due to this PR https://github.com/python/cpython/pull/25069
ATLEAST_310 = sys.version_info >= (3, 10)
