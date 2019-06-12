# """
# Useful for to convert object to boxed types.
# """
import typing

from .expressions import *
from .matching import *

__all__ = ["convert_identity_rule"]
T = typing.TypeVar("T")


@expression
def convert(type: typing.Type[T], value: object) -> T:
    """
    Converts a value to a certain type.
    """
    ...


@rule
def convert_identity_rule(t: typing.Type[T], value: T) -> R[T]:
    """
    When the value is an instance of the type being converted, we can convert it.
    """
    return convert(t, value), lambda: value

