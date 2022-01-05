"""
We represent code flags as a set of literal strings, representing each
compiler flag. 
"""
from __future__ import annotations

import dis
import enum
import __future__  # isort:skip
from typing import Set


__all__ = ["FlagsData", "to_flags_data", "from_flags_data"]

FlagsData = Set[str]


def to_flags_data(flags: int) -> FlagsData:
    flags_data: FlagsData = set()
    if not flags:
        # Don't iterate if no flags are set
        return flags_data
    # Iterate through all flags, raising an exception if we hit any unknown ones
    for f in enum._decompose(CodeFlag, flags)[0]:  # type: ignore
        if f not in CodeFlag:
            raise ValueError(f"Flag {f} is not a known flag")
        flags_data.add(f.name)
    return flags_data


def from_flags_data(flags_data: FlagsData) -> int:
    flags = 0
    for f in flags_data:
        flags |= getattr(CodeFlag, f)
    return flags


# Use an IntFlag so we can convert easily from ints
# Note that this will not raise an error on unknown flags
CodeFlag = enum.IntFlag(  # type: ignore
    "CodeFlag",
    # Compiler flags
    [(name, i) for i, name in dis.COMPILER_FLAG_NAMES.items()]
    # Other future compiler flags
    + [
        (name, getattr(__future__, name).compiler_flag)
        for name in __future__.all_feature_names
        if name
        not in {
            # Ignore nested scopes future flag since it is already
            # set as a compiler flag. I am not sure why these overlap
            "nested_scopes",
            # Ignore generators since its disabled by having the flag of 0
            "generators",
        }
    ],
)
