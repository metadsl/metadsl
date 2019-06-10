from __future__ import annotations

import inspect
import typing
import copy
import typing_inspect
import collections.abc
from .dict_tools import *

__all__ = [
    "get_type",
    "get_arg_hints",
    "GenericCheck",
    "infer",
    "TypeVarMapping",
    "OfType",
    "ExpandedType",
]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class GenericCheckType(type):
    def __subclasscheck__(cls, sub):
        """
        Modified from https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L707-L717
        """
        sub = getattr(sub, "__origin__", sub)
        if hasattr(cls, "__origin__"):
            return issubclass(sub, cls)

        # Needed when checking if T is instance of Expression
        if isinstance(sub, typing.TypeVar):  # type: ignore
            return False
        return super().__subclasscheck__(sub)


class GenericCheck(metaclass=GenericCheckType):
    """
    Subclass this to support isinstance and issubclass checks with generic classes.
    """

    pass


class OfType(GenericCheck, typing.Generic[T]):
    """
    OfType[T] should be considered a subclass of T even though it is not.
    """

    pass


class ExpandedType(GenericCheck, typing.Generic[T]):
    """
    ExpandedType should be thought of as being expanded when passed into a function,
    so that `fn(ExpandedType[int]())` will be thought of as `fn(*xs)` where xs is an iterable of `int`.
    """

    pass


# Allow isinstance and issubclass calls on generic types
def generic_subclasscheck(self, cls):
    """
    Modified from https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L707-L717
    """
    cls = getattr(cls, "__origin__", cls)
    return issubclass(self.__origin__, cls)


typing._GenericAlias.__subclasscheck__ = generic_subclasscheck  # type: ignore


def get_origin(t: typing.Type) -> typing.Type:
    origin = typing_inspect.get_origin(t)
    # Need workaround for iterables
    # https://github.com/ilevkivskyi/typing_inspect/issues/36
    if origin == collections.abc.Iterable:
        return typing.Iterable
    return origin


def get_type(v: T) -> typing.Type[T]:
    """
    Returns the type of the value with generic arguments preserved.
    """
    return typing_inspect.get_generic_type(v)


TypeVarMapping = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_type(hint: typing.Type[T], value: T) -> TypeVarMapping:
    if typing_inspect.get_origin(hint) == type:
        inner_hint, = typing_inspect.get_args(hint)
        return match_types(inner_hint, typing.cast(typing.Type, value))
    return match_types(hint, typing_inspect.get_generic_type(value))


def match_types(hint: typing.Type, t: typing.Type) -> TypeVarMapping:
    """
    Matches a type hint with a type, return a mapping of any type vars to their values.
    """
    # If it is an instance of OfType[Type[T]], then we should consider it as T
    if isinstance(t, OfType):
        of_type, = typing_inspect.get_args(typing_inspect.get_generic_type(t))
        assert issubclass(of_type, typing.Type)
        t, = typing_inspect.get_args(of_type)
        return match_types(hint, t)

    # If the type is an OfType[T] then we should really just consider it as T
    if issubclass(t, OfType) and not issubclass(hint, OfType):
        t, = typing_inspect.get_args(t)
        return match_types(hint, t)

    # Matching an expanded type is like matching just whatever it represents
    if issubclass(t, ExpandedType):
        t, = typing_inspect.get_args(t)

    if typing_inspect.is_typevar(hint):
        return {hint: t}

    if not issubclass(t, hint):
        raise TypeError(f"Cannot match concrete type {t} with hint {hint}")
    return safe_merge(
        *(
            match_types(inner_hint, inner_t)
            for inner_hint, inner_t in zip(
                typing_inspect.get_args(hint), typing_inspect.get_args(t)
            )
        )
    )


def get_origin_type(t: typing.Type) -> typing.Type:
    """
    Takes in a type, and if it is a generic type, returns the original type hint.

    typing.List[int] -> typing.List[T]
    """
    t = get_origin(t) or t

    params = typing_inspect.get_parameters(t)
    if params:
        return t[params]
    return t


T_type = typing.TypeVar("T_type", bound=typing.Type)


def replace_typevars(typevars: TypeVarMapping, hint: T_type) -> T_type:
    """
    Replaces type vars in a type hint with other types.
    """
    if typing_inspect.is_typevar(hint):
        return typing.cast(T_type, typevars.get(hint, hint))
    args = typing_inspect.get_args(hint)
    if not args:
        return hint
    replaced_args = tuple(replace_typevars(typevars, arg) for arg in args)
    return get_origin(hint)[replaced_args]


def get_arg_hints(fn: typing.Callable) -> typing.List[typing.Type]:
    signature = inspect.signature(fn)
    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(fn)
    return [hints[param] for param in signature.parameters.keys()]


def infer_return_type(
    fn: typing.Callable[..., T],
    args: typing.Tuple[object, ...],
    kwargs: typing.Mapping[str, object],
) -> typing.Tuple[
    typing.Tuple[object, ...], typing.Mapping[str, object], typing.Type[T]
]:

    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(fn)

    signature = inspect.signature(fn)

    param_names = list(signature.parameters.keys())
    # This is the self arg, infer it from the first arg type
    if param_names and param_names[0] not in hints:
        hints[param_names[0]] = get_origin_type(get_type(args[0]))

    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()

    # We need to edit the arguments to pop off the variable one
    arguments = copy.copy(bound.arguments)

    for arg_name, p in signature.parameters.items():
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            variable_args = arguments.pop(arg_name)
            argument_items = list(arguments.items())
            argument_items += [(arg_name, a) for a in variable_args]
            break
    else:
        argument_items = list(arguments.items())

    return_hint: typing.Type[T] = hints.pop("return")

    mappings: typing.List[TypeVarMapping] = [
        match_type(hints[name], arg) for name, arg in argument_items
    ]
    try:
        matches: TypeVarMapping = safe_merge(*mappings)
    except ValueError:
        raise TypeError(f"Couldn't merge mappings {mappings}")

    return bound.args, bound.kwargs, replace_typevars(matches, return_hint)


def infer(
    fn: typing.Callable[..., T]
) -> typing.Callable[
    ...,
    typing.Tuple[
        typing.Tuple[object, ...], typing.Mapping[str, object], typing.Type[T]
    ],
]:
    """
    Wraps a function to return the args, kwargs, and the inferred return type based
    on the arguments.

    This raise a TypeError when called with types that are invalid.

    It refers on the explicit generic types of the arguments, it does not traverse
    them to check their types. That means if you pass in `[1, 2, 3]` it won't know
    this is a `typing.List[int]`. Instead it, will only know if you create a generic
    instance manually from a custom generic class like, `MyList[int](1, 2, 3)`.

    >>> def fn(a: T) -> typing.List[T]:
        ...
    >>> infer(fn)(10)
    ((10,), {}, typing.List[int])
    """

    def infer_inner(*args, __fn=fn, **kwargs):
        return infer_return_type(__fn, args, kwargs)

    return infer_inner
