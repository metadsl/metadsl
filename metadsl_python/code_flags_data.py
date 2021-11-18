from __future__ import annotations

from dataclasses import astuple, dataclass
from dis import COMPILER_FLAG_NAMES
from typing import List
import __future__  # isort:skip


@dataclass
class CodeFlagsData:
    """
    This class represents the flags enabled for a certain code block.

    It decodes the bits that Python uses to store the flags into a number
    of boolean options, to make it more explicit.

    As well as including the documented bytecode flags, it also include all
    the future flags, which are also added in the byte string.
    """

    # The code object is optimized, using fast locals.
    optimized: bool
    # If set, a new dict will be created for the frame’s f_locals when the code
    # object is executed.
    newlocals: bool
    # The code object has a variable positional parameter (*args-like).
    varargs: bool
    # The code object has a variable keyword parameter (**kwargs-like).
    varkeywords: bool
    # The flag is set when the code object is a nested function.
    nested: bool
    # The flag is set when the code object is a generator function, i.e. a
    # generator object is returned when the code object is executed.
    generator: bool
    # The flag is set if there are no free or cell variables.
    nofree: bool
    # The flag is set when the code object is a coroutine function. When the
    # code object is executed it returns a coroutine object. See PEP 492 for
    # more details.
    coroutine: bool
    # The flag is used to transform generators into generator-based coroutines.
    # Generator objects with this flag can be used in await expression, and can
    # yield from coroutine objects. See PEP 492 for more details.
    iterable_coroutine: bool
    # The flag is set when the code object is an asynchronous generator
    # function. When the code object is executed it returns an asynchronous
    # generator object. See PEP 525 for more details.
    async_generation: bool

    # These flags all represent different future imports that are active
    # https://docs.python.org/3/library/__future__.html#module-__future__
    future_division: bool
    future_absolute_import: bool
    future_with_statement: bool
    future_print_function: bool
    future_unicode_literals: bool
    future_barry_as_bdfl: bool
    future_generator_stop: bool
    future_annotations: bool

    @classmethod
    def from_flags(cls, flags: int) -> CodeFlagsData:
        return cls(*(bool(flags & flag) for flag in FLAG_VALUES),)

    def to_flags(self) -> int:
        flags = 0
        for is_enabled, value in zip(astuple(self), FLAG_VALUES):
            if is_enabled:
                flags += value
        return flags


FUTURE_FLAG_NAMES = [
    "CO_FUTURE_DIVISION",
    "CO_FUTURE_ABSOLUTE_IMPORT",
    "CO_FUTURE_WITH_STATEMENT",
    "CO_FUTURE_PRINT_FUNCTION",
    "CO_FUTURE_UNICODE_LITERALS",
    "CO_FUTURE_BARRY_AS_BDFL",
    "CO_FUTURE_GENERATOR_STOP",
    "CO_FUTURE_ANNOTATIONS",
]

# List of flag values, in order of the dataclass
FLAG_VALUES: List[int] = [
    *COMPILER_FLAG_NAMES.keys(),
    *(getattr(__future__, name) for name in FUTURE_FLAG_NAMES),
]
