from __future__ import annotations

import typing
import typing_inspect
import inspect


from .dict_tools import *

__all__ = ["infer_return_type", "get_type", "get_arg_hints", "GenericCheck"]
T = typing.TypeVar("T")



class GenericCheckType(type):
    def __subclasscheck__(cls, sub):
        """
        Modified from https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L707-L717
        """
        sub = getattr(sub, "__origin__", sub)
        if hasattr(cls, "__origin__"):
            return issubclass(sub, cls)
        return super().__subclasscheck__(sub)


class GenericCheck(metaclass=GenericCheckType):
    """
    Subclass this to support isinstance and issubclass checks with generic classes.
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


def get_type(v: T) -> typing.Type[T]:
    """
    Returns the type of the value with generic arguments preserved.
    """
    return typing_inspect.get_generic_type(v)


typevar_mapping_typing = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_types(hint: typing.Type, t: typing.Type) -> typevar_mapping_typing:
    """
    Matches a type hint with a type, return a mapping of any type vars to their values.
    """
    if typing_inspect.is_typevar(hint):
        return {hint: t}
    if typing_inspect.is_union_type(hint):
        l, r = typing_inspect.get_args(hint)
        try:
            return match_types(l, t)
        except TypeError:
            pass

        try:
            return match_types(r, t)
        except TypeError:
            raise TypeError(f"Cannot match type {t} with hint {hint}")

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


def get_arg_hints(
    fn: typing.Callable, first_arg_type: typing.Optional[typing.Type] = None
) -> typing.Tuple[typing.Type, ...]:
    """
    Returns back the arg type hints.
    """
    hints = typing.get_type_hints(fn)
    arg_hints: typing.List[typing.Type] = []
    for arg_name in inspect.signature(fn).parameters.keys():

        # Special case for inferring type hint for self arg, by looking at type of first arg
        if arg_name == "self" and first_arg_type is not None:
            new_self_hint = typing_inspect.get_origin(first_arg_type) or first_arg_type

            params = typing_inspect.get_parameters(new_self_hint)
            if params:
                new_self_hint = new_self_hint[
                    typing_inspect.get_parameters(new_self_hint)
                ]
            arg_hints.append(new_self_hint)
            continue

        arg_hints.append(hints[arg_name])
    return tuple(arg_hints)


def infer_return_type(
    fn: typing.Callable[..., T], *arg_types: typing.Type
) -> typing.Type[T]:
    """
    Returns the infered return type of the function, based on it's argument types,
    by looking at the type signature and matching generics.
    """
    arg_hints = get_arg_hints(fn, arg_types[0] if arg_types else None)
    return_hint = typing.get_type_hints(fn)["return"]

    matches: typevar_mapping_typing = safe_merge(
        *(
            match_types(arg_hint, arg_type)
            for arg_hint, arg_type in zip(arg_hints, arg_types)
            if arg_hint is not None
        )
    )
    return replace_typevars(matches, return_hint)
