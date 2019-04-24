# import typing

# import functools

# __all__ = ["memoize", "unsafe_hash"]
# T = typing.TypeVar("T", bound=typing.Callable)


# def unsafe_hash(o: object) -> int:
#     """
#     Hash that always works, based on hash or id.

#     Uses meomoized __unsafe_hash__ attribute of classes
#     if possible.
#     """
#     try:
#         return o.__unsafe_hash__  # type: ignore
#     except AttributeError:
#         pass

#     try:
#         return hash(o)
#     except TypeError:
#         return hash(id(o))


# def memoize(fn: T) -> T:
#     """
#     Decorator to memoize a function that takes one arg, based on the id of the argument.

#     Kwargs are passed through.
#     """
#     values: typing.Dict[int, object] = {}

#     @functools.wraps(fn)
#     def inner(a, **kwargs):
#         i = unsafe_hash(a)
#         if i in values:
#             return values[i]
#         res = fn(a, **kwargs)
#         values[i] = res
#         return res

#     return typing.cast(T, inner)
