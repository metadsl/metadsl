from __future__ import annotations

import inspect
import typing
import copy
import typing_inspect
import collections.abc
import dataclasses
import functools
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


typing._GenericAlias.__getattr__ = generic_getattr  # type: ignore


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

    if typing_inspect.is_typevar(t):
        return {}

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
    instance: object,
    owner: typing.Optional[typing.Type],
    args: typing.Tuple[object, ...],
    kwargs: typing.Mapping[str, object],
) -> typing.Tuple[
    # type of owner, with typevars replaced
    typing.Optional[typing.Type],
    typing.Tuple[object, ...],
    typing.Mapping[str, object],
    typing.Type[T],
]:

    # Get inner function if we have one, like if this is a classmethod
    inner_fn = getattr(fn, "__func__", fn)
    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(inner_fn)
    signature = inspect.signature(inner_fn)

    is_classmethod = isinstance(fn, classmethod)
    if is_classmethod:
        assert owner and not instance

    # This case is triggered if we got here from a __get__ call
    # in a descriptor
    if owner:
        first_arg_name = next(iter(signature.parameters.keys()))
        if is_classmethod:
            # If we called this as a class method, add the owner to
            # the args add the inferred type to the hints.
            args = (owner,) + args  # type: ignore
            first_arg_type = typing.Type[get_origin_type(owner)]  # type: ignore
        elif instance:
            # If we have called this as a method, then add the instance
            # to the args and infer the type hint for this first arg
            args = (instance,) + args
            first_arg_type = get_origin_type(get_type(instance))
        # we are calling an instance method on the class and passing the instance as the first arg
        else:
            first_arg_type = get_origin_type(get_type(args[0]))

        if first_arg_name not in hints:
            hints[first_arg_name] = first_arg_type

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

    return (
        replace_typevars(matches, get_origin_type(owner))  # type: ignore
        if is_classmethod
        else None,
        # Remove first arg if it was a classmethod
        bound.args[1:] if is_classmethod else bound.args,
        bound.kwargs,
        replace_typevars(matches, return_hint),
    )


WrapperType = typing.Callable[
    [
        typing.Callable[..., T],
        typing.Tuple[object, ...],
        typing.Mapping[str, object],
        typing.Type[T],
    ],
    U,
]


@dataclasses.dataclass
class Infer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]

    def __post_init__(self):
        functools.update_wrapper(self, self.fn)

    def __call__(self, *args, **kwargs) -> U:
        return self.wrapper(  # type: ignore
            self, *infer_return_type(self.fn, None, None, args, kwargs)[1:]
        )

    def __get__(self, instance, owner) -> BoundInfer[T, U]:
        return BoundInfer(self.fn, self.wrapper, instance, owner)  # type: ignore


@dataclasses.dataclass
class BoundInfer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]
    instance: object
    owner: typing.Type

    def __call__(self, *args, **kwargs) -> U:
        owner_replaced, *rest = infer_return_type(
            self.fn, self.instance, self.owner, args, kwargs
        )
        return self.wrapper(  # type: ignore
            # Normalize this method so that equality checks on the returned function are consistant:
            # * Remove the instance, because it is already present in the args
            # * Remove the params from the owner, if in a method, because they are present on the arg.
            # * Add the params to the owner, by using type of first arg, if we are in a classmethod, since that isn't in the args
            dataclasses.replace(  # type: ignore
                self,
                instance=None,
                owner=owner_replaced
                if isinstance(self.fn, classmethod)
                else get_origin(self.owner) or self.owner,
            ),
            *rest,
        )


def infer(
    fn: typing.Callable[..., T], wrapper: WrapperType[T, U]
) -> typing.Callable[..., U]:
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
    >>> infer(fn, lambda *args: args)(10)
    ((10,), {}, typing.List[int])
    """

    return Infer(fn, wrapper)
