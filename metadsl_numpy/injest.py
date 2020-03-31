from __future__ import annotations

import functools
import typing

from metadsl import *
from metadsl_core import *

from .boxing import *

__all__ = ["injest", "guess_type", "guess_first_type"]


T = typing.TypeVar("T")
U = typing.TypeVar("U")


def injest(
    o: object, compat_type: typing.Type[T] = None, inner_type: typing.Type[U] = None
) -> T:
    """
    Returns a metadsl expression that is roughly compatible with the Python object.

    Shouldn't be used in real code, because it cannot be properly
    typed. However, it can be used in notebook for exploration
    """
    if not compat_type or not inner_type:
        compat_type, inner_type = guess_type(o)

    b = typing.cast(Boxer[T, U], Boxer[compat_type, inner_type])  # type: ignore
    return b.convert_and_box(o)


@functools.singledispatch
def guess_type(o: object) -> typing.Tuple[typing.Type, typing.Type]:
    raise NotImplementedError(
        f"Don't know how to guess type {type(o)}, provide an explicit type to injest."
    )


def guess_first_type(*os: object) -> typing.Tuple[typing.Type, typing.Type]:
    for o in os:
        try:
            return guess_type(o)
        except NotImplementedError:
            continue
    raise NotImplementedError(f"Cannot guess types for any of {os}")
