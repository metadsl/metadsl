from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Union
from itertools import chain


@dataclass
class NewLineTable:
    """
    PEP 626 line number table.
    """

    bytes: bytes

    def to_bytes(self) -> bytes:
        return self.bytes


@dataclass
class OldLineTable:
    """
    Pre PEP 626 line number mapping
    """

    items: list[LineTableItem]

    @classmethod
    def from_bytes(cls, bytes: bytes) -> OldLineTable:
        """
        Constructs a line table from a byte string.
        """
        items = []
        for i in range(0, len(bytes), 2):
            items.append(LineTableItem(bytes[i], bytes[i + 1]))
        return OldLineTable(items)

    def to_bytes(self) -> bytes:
        """
        Converts the line table to a byte string.
        """
        return bytes(chain.from_iterable(self.items))


@dataclass
class LineTableItem:
    line_offset: int
    bytecode_offset: int

    def __iter__(self) -> Iterator[int]:
        yield self.line_offset
        yield self.bytecode_offset


LineTable = Union[NewLineTable, OldLineTable]
