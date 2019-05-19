from __future__ import annotations

import typing
import typing_inspect
import inspect
import functools
import dataclasses

from .dict_tools import *

__all__ = ["get_type", "get_arg_hints", "GenericCheck", "infer"]
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
        return super().__subclasscheck__(sub)


class GenericCheck(metaclass=GenericCheckType):
    """
    Subclass this to support isinstance and issubclass checks with generic classes.
    """

    pass


original_generic_getattr = typing._GenericAlias.__getattr__  # type: ignore


def generic_getattr(self, attr):
    """
    Allows classmethods to get generic types
    by checking if we are getting a descriptor type
    and if we are, we pass in the generic type as the class
    instead of the origin type.

    Modified from
    https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L694-L699
    """

    if "__origin__" in self.__dict__ and not typing._is_dunder(attr):  # type: ignore
        # If the attribute is a descriptor, pass in the generic class
        property = self.__origin__.__getattribute__(self.__origin__, attr)
        if hasattr(property, "__get__"):
            return property.__get__(None, self)
        # Otherwise, just resolve it normally
        return getattr(self.__origin__, attr)
    raise AttributeError(attr)


# Allow isinstance and issubclass calls on generic types
def generic_subclasscheck(self, cls):
    """
    Modified from https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L707-L717
    """
    cls = getattr(cls, "__origin__", cls)
    return issubclass(self.__origin__, cls)


typing._GenericAlias.__subclasscheck__ = generic_subclasscheck  # type: ignore
typing._GenericAlias.__getattr__ = generic_getattr  # type: ignore


def get_type(v: T) -> typing.Type[T]:
    """
    Returns the type of the value with generic arguments preserved.
    """
    return typing_inspect.get_generic_type(v)


typevar_mapping_typing = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_type(hint: typing.Type[T], value: T) -> typevar_mapping_typing:
    if typing_inspect.get_origin(hint) == type:
        inner_hint, = typing_inspect.get_args(hint)
        return match_types(inner_hint, typing.cast(typing.Type, value))
    return match_types(hint, typing_inspect.get_generic_type(value))


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


def get_origin_type(t: typing.Type) -> typing.Type:
    """
    Takes in a type, and if it is a generic type, returns the original type hint.

    typing.List[int] -> typing.List[T]
    """
    t = typing_inspect.get_origin(t) or t

    params = typing_inspect.get_parameters(t)
    if params:
        return t[params]
    return t


T_type = typing.TypeVar("T_type", bound=typing.Type)


def replace_typevars(typevars: typevar_mapping_typing, hint: T_type) -> T_type:
    """
    Replaces type vars in a type hint with other types.
    """
    if typing_inspect.is_typevar(hint):
        return typing.cast(T_type, typevars.get(hint, hint))
    args = typing_inspect.get_args(hint)
    if not args:
        return hint
    replaced_args = tuple(replace_typevars(typevars, arg) for arg in args)
    return typing_inspect.get_origin(hint)[replaced_args]


def get_arg_hints(fn: typing.Callable) -> typing.List[typing.Type]:
    signature = inspect.signature(fn)
    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(fn)
    return [hints[param] for param in signature.parameters.keys()]


def infer_return_type(
    fn: typing.Callable[..., T],
    instance: object,
    owner: typing.Optional[typing.Type],
    args: typing.Tuple[object, ...],
    kwargs: typing.Mapping[str, object],
) -> typing.Tuple[
    typing.Tuple[object, ...], typing.Mapping[str, object], typing.Type[T]
]:

    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(fn)

    signature = inspect.signature(fn)

    # This case is triggered if we got here from a __get__ call
    # in a descriptor
    if owner:
        first_arg_name = next(iter(signature.parameters.keys()))
        if instance:
            # If we have called this as a method, then add the instance
            # to the args and infer the type hint for this first arg
            args = (instance,) + args
            if first_arg_name not in hints:
                hints[first_arg_name] = get_origin_type(get_type(instance))
        else:
            # If we called this as a class method, add the owner to
            # the args add the inferred type to the hints.
            args = (owner,) + args  # type: ignore
            if first_arg_name not in hints:
                hints[first_arg_name] = typing.Type[get_origin_type(owner)]

    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()

    # We need to edit the arguments to pop off the variable one
    arguments = bound.arguments

    for arg_name, p in signature.parameters.items():
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            variable_args = arguments.pop(arg_name)
            argument_items = list(arguments.items())
            argument_items += [(arg_name, a) for a in variable_args]
            break
    else:
        argument_items = list(arguments.items())

    return_hint: typing.Type[T] = hints.pop("return")

    mappings: typing.List[typevar_mapping_typing] = [
        match_type(hints[name], arg) for name, arg in argument_items
    ]
    try:
        matches: typevar_mapping_typing = safe_merge(*mappings)
    except ValueError:
        raise TypeError(f"Couldn't merge mappings {mappings}")
    args = bound.args
    # Remove first arg if it was a class.
    if owner and not instance:
        args = args[1:]
    return args, bound.kwargs, replace_typevars(matches, return_hint)


WrapperType = typing.Callable[
    [
        typing.Callable[..., T],
        typing.Tuple[object, ...],
        typing.Mapping[str, object],
        typing.Type[T],
    ],
    U,
]


@dataclasses.dataclass(repr=False)
class Infer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]

    def __post_init__(self):
        # This case is if we are wrapping a classmethod.
        # We should grab the original function, so we can inspect
        # it's signature
        if isinstance(self.fn, classmethod):
            self.fn = self.fn.__func__

        functools.update_wrapper(self, self.fn)

    def __call__(self, *args, **kwargs) -> U:
        return self.wrapper(  # type: ignore
            self.fn, *infer_return_type(self.fn, None, None, args, kwargs)
        )

    def __get__(self, instance, owner) -> BoundInfer[T, U]:
        return BoundInfer(self.fn, self.wrapper, instance, owner)  # type: ignore


@dataclasses.dataclass(repr=False)
class BoundInfer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]
    instance: object
    owner: typing.Type

    def __call__(self, *args, **kwargs) -> U:
        return self.wrapper(  # type: ignore
            self.fn,
            *infer_return_type(self.fn, self.instance, self.owner, args, kwargs),
        )


def infer(fn: typing.Callable[..., T], wrapper: WrapperType[T, U]) -> typing.Callable:
    """
    Wraps a function to return the args, kwargs, and the inferred return type based
    on the arguments.

    Note that this works with classmethod but must be placed above them until
    https://github.com/python/cpython/pull/8405 is merged.

    This raise a TypeError when called with types that are invalid.

    It refers on the explicit generic types of the arguments, it does not traverse
    them to check their types. That means if you pass in `[1, 2, 3]` it won't know
    this is a `typing.List[int]`. Instead it, will only know if you create a generic
    instance manually from a custom generic class like, `MyList[int](1, 2, 3)`.

    >>> def fn(a: T) -> typing.List[T]:
        ...
    >>> infer(fn, lambda fn, args, kwargs, return_type: args, kwargs, return_type)(10)
    ((10,), {}, typing.List[int])
    """
    return Infer(fn, wrapper)
