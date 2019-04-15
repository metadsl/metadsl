import typing

import functools

__all__ = ["memoize"]
T = typing.TypeVar("T", bound=typing.Callable)


def memoize(fn: T) -> T:
    """
    Decorator to memoize a function that takes one arg, based on the id of the argument.

    Kwargs are passed through.
    """
    values: typing.Dict[int, object] = {}

    @functools.wraps(fn)
    def inner(a, **kwargs):
        i = id(a)
        if i in values:
            return values[i]
        res = fn(a, **kwargs)
        values[i] = res
        return res

    return typing.cast(T, inner)
