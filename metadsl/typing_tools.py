from __future__ import annotations

import typing
import typing_inspect
import inspect


from .dict_tools import *

__all__ = ["infer_return_type", "get_type", "get_type_hints"]
T = typing.TypeVar("T")


def get_type(v: T) -> typing.Type[T]:
    """
    Returns the type of the value with generic arguments preserved.
    """
    return typing_inspect.get_generic_type(v)


# MYPY: ???
typevar_mapping_typing = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_types(hint: typing.Type, t: typing.Type) -> typevar_mapping_typing:
    """
    Matches a type hint with a type, return a mapping of any type vars to their values.
    """
    if typing_inspect.is_typevar(hint):
        return {hint: t}
    return safe_merge(
        *(
            match_types(inner_hint, inner_t)
            for inner_hint, inner_t in zip(
                typing_inspect.get_args(hint), typing_inspect.get_args(t)
            )
        )
    )


def replace_typevars(
    typevars: typevar_mapping_typing, hint: typing.Type
) -> typing.Type:
    """
    Replaces type vars in a type hint with other types.
    """
    if typing_inspect.is_typevar(hint):
        return typevars.get(hint, hint)
    args = typing_inspect.get_args(hint)
    if not args:
        return hint
    replaced_args = tuple(replace_typevars(typevars, arg) for arg in args)
    return typing_inspect.get_origin(hint)[replaced_args]


def get_type_hints(
    fn: typing.Callable
) -> typing.Tuple[typing.Tuple[typing.Optional[typing.Type], ...], typing.Type]:
    """
    Returns back the arg type hints and return type hints for a function.

    Arg types are None if they are not supplied.
    """
    hints = typing.get_type_hints(fn)
    arg_hints: typing.List[typing.Optional[typing.Type]] = []
    for arg_name in inspect.signature(fn).parameters.keys():
        arg_hints.append(hints.get(arg_name, None))
    return tuple(arg_hints), hints.get("return", None)


def infer_return_type(
    fn: typing.Callable[..., T], *arg_types: typing.Type
) -> typing.Type[T]:
    """
    Returns the infered return type of the function, based on it's argument types,
    by looking at the type signature and matching generics.
    """
    arg_hints, return_hint = get_type_hints(fn)

    matches: typevar_mapping_typing = safe_merge(
        *(
            match_types(arg_hint, arg_type)
            for arg_hint, arg_type in zip(arg_hints, arg_types)
            if arg_hint is not None
        )
    )
    return replace_typevars(matches, return_hint)
