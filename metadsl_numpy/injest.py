from __future__ import annotations

import functools
import typing

from metadsl import *
from metadsl_core import *

__all__ = ["injest", "guess", "guess_all", "Guess"]


T = typing.TypeVar("T")
U = typing.TypeVar("U")

Guess = typing.Tuple[Maybe[T], typing.Callable[[Maybe[T]], U]]


def injest(o: object) -> object:
    """
    Returns a metadsl expression that is roughly compatible with the Python object.

    Shouldn't be used in real code.
    """
    inner_version, to_outer_version = guess(o)
    return to_outer_version(inner_version)


@functools.singledispatch
def guess(o: object) -> Guess:
    """
    Takes in an object and returns the guessed inner type, and a callable that takes
    that and returns the compat type
    """
    raise NotImplementedError(
        f"Don't know how to guess type {type(o)}, provide an explicit type to injest."
    )


def guess_all(
    o: object, *os: object
) -> typing.Tuple[typing.Callable[[Maybe[T]], object], typing.List[Maybe[T]]]:
    """
    Guesses all and makes sure they have the same callable.
    """
    result, make_outer = guess(o)
    results = [result]
    for o in os:
        result, new_make_outer = guess(o)
        if new_make_outer != make_outer:
            raise NotImplementedError(f"different guesses for {(o,) + os}")
        results.append(result)
    return make_outer, results
