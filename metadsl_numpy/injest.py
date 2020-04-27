from __future__ import annotations

import functools
import typing

from metadsl import *
from metadsl_core import *

from .boxing import *

__all__ = ["injest", "guess_type", "guess_types", "guess_type_of_type"]


T = typing.TypeVar("T")
U = typing.TypeVar("U")


def injest(o: object) -> object:
    """
    Returns a metadsl expression that is roughly compatible with the Python object.

    Shouldn't be used in real code.
    """
    compat_tp, inner_tp = guess_type(o)
    return Boxer[compat_tp, inner_tp].convert_and_box(o)  # type: ignore


@functools.singledispatch
def guess_type(o: object) -> typing.Tuple[typing.Type, typing.Type]:
    """
    Takes in an object and returns a typle of the outer compat type and inner type.
    """
    raise NotImplementedError(
        f"Don't know how to guess type {type(o)}, provide an explicit type to injest."
    )


def guess_types(o: object, *os: object) -> typing.Tuple[typing.Type, typing.Type]:
    """
    Guesses all and makes sure they have they have the same types
    """
    compat_tp, inner_tp = guess_type(o)
    for o in os:
        new_compat_tp, new_inner_tp = guess_type(o)
        if (compat_tp != new_compat_tp) or (inner_tp != new_inner_tp):
            raise NotImplementedError(f"different guesses for {(o,) + os}")
    return compat_tp, inner_tp


class CreateInstance(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def create(cls) -> T:
        ...


def create_instance(tp: typing.Type[T]) -> T:
    return CreateInstance[tp].create()  # type: ignore


def guess_type_of_type(tp: typing.Type) -> typing.Tuple[typing.Type, typing.Type]:
    """
    Guesses the type of a type, by creating a dummy instance of it and guessing the type of that.

    We need this b/c functools.singledispatch doesn't really work at the type level, so we just make
    dummy instances instead.
    """
    return guess_type(create_instance(tp))
