"""
Decodes the linear list of instructions into a control flow graph.

This representation is a list blocks, where each block is a list of instructions.
We keep a mapping from the bytecode offset, which is the value in the jump
instructions, to the block index.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from .instruction_data import (
    instructions_from_bytes,
    instructions_to_bytes,
    InstructionData,
)


def bytes_to_cfg(b: bytes) -> ControlFlowGraph:
    return ControlFlowGraph.from_instructions(*instructions_from_bytes(b))


def cfg_to_bytes(cfg: ControlFlowGraph) -> bytes:
    return instructions_to_bytes(cfg.to_instructions())


@dataclass
class ControlFlowGraph:
    """
    The control flow graph represents the different "blocks" of instructions
    that Python moves between as it executes the control flow.

    Every instruction that is jumped to starts a new control flow block.
    Every jump and return instructions ends a control flow block.
    """

    # Ordered mapping of bytecode offset to "block"
    blocks: dict[int, list[InstructionData]]

    def verify(self) -> None:
        """
        Verify that the control flow graph is valid, by making sure every
        instruction that jumps can find it's block and that each block
        has the proper instructions in it
        """
        prev_block = None
        for offset, block in self.blocks.items():
            # Verify block is not empty
            assert block, f"Block at offset {offset} is empty"
            # Verify all instructions in this block are after the offset
            for instruction in block:
                if instruction.jump_target_offset is not None:
                    assert (
                        instruction.jump_target_offset in self.blocks
                    ), "Jump target not in block mapping"

                for o in instruction.offsets():
                    assert (
                        o >= offset
                    ), "Instruction in this block is before this blocks offset"
            # Verify all instructions in previous block are before this offset
            if prev_block is not None:
                for i in prev_block:
                    for o in i.offsets():
                        assert (
                            o < offset
                        ), "Instruction in previous block is after this blocks offset"
            prev_block = block

    @classmethod
    def from_instructions(cls, *instructions: InstructionData) -> ControlFlowGraph:
        # First compute a sorted list of all bytecode offsets which are jump targets
        # plus the initial offset of 0
        targets = sorted(
            set(
                i.jump_target_offset
                for i in instructions
                if i.jump_target_offset is not None
            )
            | {0}
        )
        blocks: dict[int, list[InstructionData]] = {i: [] for i in targets}
        current_block_index = -1
        # Then, iterate through each instruction, creating a new block of its a jump target
        for instruction in instructions:
            # There is another block after this one, if the targets contains another offset
            try:
                next_block_offset = targets[current_block_index + 1]
            except IndexError:
                pass
            else:
                # This instruction starts the next block, if the next blocks offets
                # is one of this instruction's offsets
                instruction_starts_next_block = next_block_offset in set(
                    instruction.offsets()
                )
                if instruction_starts_next_block:
                    current_block_index += 1
            blocks[targets[current_block_index]].append(instruction)

        return cls(blocks)

    def to_instructions(self) -> Iterable[InstructionData]:
        for block in self.blocks.values():
            yield from block
