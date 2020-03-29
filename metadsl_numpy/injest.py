from __future__ import annotations

import functools
import typing

from metadsl import *
from metadsl_core import *

__all__ = ["injest", "guess_type"]


T = typing.TypeVar("T")


def injest(o: object, t: typing.Optional[typing.Type[T]] = None) -> T:
    """
    Returns a metadsl expression that is roughly compatible with the Python object.

    Shouldn't be used in real code, because it cannot be properly
    typed. However, it can be used in notebook for exploration
    """
    if not t:
        t = guess_type(o)
    return (
        typing.cast(
            typing.Type[Converter[T]], Converter[t]  # type: ignore
        )
        .convert(o)
        .assert_
    )


@functools.singledispatch
def guess_type(o: object) -> typing.Type:
    raise NotImplementedError(
        f"Don't know how to guess type {type(o)}, provide an explicit type to injest."
    )
