from __future__ import annotations

import inspect
import typing
import copy
import typing_inspect
import collections.abc
import dataclasses
import functools
import types
from .dict_tools import *

__all__ = [
    "get_type",
    "get_arg_hints",
    "GenericCheck",
    "infer",
    "TypeVarMapping",
    "OfType",
    "replace_typevars",
    "match_functions",
    "match_values",
    "BoundInfer",
    "ExpandedType",
    "replace_fn_typevars",
    "merge_typevars",
    "match_types",
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
        if sub == typing.Any:
            return False

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
    if "__origin__" in self.__dict__ and attr not in ("__wrapped__"):
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


def get_function_type(fn: typing.Callable) -> typing.Type[typing.Callable]:
    """
    Gets the type of a function:

    Only supports positional args currently

    >>> get_function_type(lambda i: i)
    typing.Callable[[typing.Any], typing.Any]

    >>> def fn(a: int, b: str) -> float: ...
    >>> get_function_type(fn)
    typing.Callable[[int, str], float]

    >>> def no_return_type(a: int, b: str): ...
    >>> get_function_type(no_return_type)
    typing.Callable[[int, str], typing.Any]

    >>> def no_arg_type(a, b: str): ...
    >>> get_function_type(no_arg_type)
    typing.Callable[[typing.Any, str], typing.Any]
    """
    signature = inspect.signature(fn)
    type_hints = typing.get_type_hints(fn)
    arg_hints: typing.List[typing.Type] = []

    for arg_name, p in signature.parameters.items():
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            arg_hints.append(type_hints.get(arg_name, typing.Any))
        else:
            raise NotImplementedError(f"Does not support getting type of {signature}")
    return typing.Callable[arg_hints, type_hints.get("return", typing.Any)]


def get_bound_infer_type(b: BoundInfer) -> typing.Type[typing.Callable]:
    """
    Returns a typing.Callable type that corresponds to the type of the bound infer.

    TODO: This logic is a combination of `get_function_type` and `infer_return_type`.
    We should eventually merge all of this into a consistant API so we don't have to duplicate this code. 
    """
    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(b.fn)
    signature = inspect.signature(b.fn)

    # We want to get the original type hints for the first arg,
    # and match those against the first arg in the bound, so we get a typevar mapping
    first_arg_name = next(iter(signature.parameters.keys()))
    typevars: TypeVarMapping
    # Whether to skip the first arg of the param of the signature when computing the signature
    skip_first_param: bool
    if b.is_classmethod:
        # If we called this as a class method
        typevars = match_type(typing.Type[b._owner_origin], b.owner)
        skip_first_param = True
    elif b.instance:
        # If we have called this as a method
        typevars = match_type(b._owner_origin, b.instance)
        skip_first_param = True
    else:
        # we are calling an instance method on the class and passing the instance as the first arg
        typevars = match_type(typing.Type[b._owner_origin], b.owner)
        skip_first_param = False
        hints[first_arg_name] = b._owner_origin

    # Then we want to replace all the typevar hints, with what we now know from the first arg
    arg_hints: typing.List[typing.Type] = []

    for arg_name, p in signature.parameters.items():
        if skip_first_param:
            skip_first_param = False
            continue
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            arg_hints.append(
                replace_typevars(
                    typevars, hints.get(arg_name, typing.cast(typing.Type, typing.Any))
                )
            )
        else:
            raise NotImplementedError(f"Does not support getting type of {signature}")
    return typing.Callable[
        arg_hints,
        replace_typevars(
            typevars, hints.get("return", typing.cast(typing.Type, typing.Any))
        ),
    ]


def get_type(v: T) -> typing.Type[T]:
    """
    Returns the type of the value with generic arguments preserved.
    """
    if isinstance(v, Infer):
        return get_function_type(v.fn)  # type: ignore
    if isinstance(v, BoundInfer):
        return get_bound_infer_type(v)  # type: ignore
    tp = typing_inspect.get_generic_type(v)
    # Special case, only support homogoneous tuple that are inferred to iterables
    if tp == tuple:
        return typing.Iterable[get_type(v[0]) if v else typing.Any]  # type: ignore
    # Special case, also support function types.
    if tp == types.FunctionType:
        return get_function_type(v)  # type: ignore

    return tp


TypeVarMapping = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_values(hint_value: T, value: T) -> TypeVarMapping:
    return match_type(get_type(hint_value), value)


def match_type(hint: typing.Type[T], value: T) -> TypeVarMapping:
    if typing_inspect.get_origin(hint) == type:
        inner_hint, = typing_inspect.get_args(hint)
        return match_types(inner_hint, typing.cast(typing.Type, value))
    return match_types(hint, get_type(value))


def merge_typevars(*typevars: TypeVarMapping) -> TypeVarMapping:
    """
    Merges typevar mappings. If there is a duplicate key, either the values should be the
    same or one should have `typing.Any` type, or one should be a typevar itself. If it is a typevar,
    that typevar is also set to the other's value
    """
    merged: TypeVarMapping = {}
    typevars_: typing.List[TypeVarMapping] = list(typevars)
    while typevars_:
        tvs: TypeVarMapping = typevars_.pop()
        for tv, tp in tvs.items():  # type: ignore
            if tv not in merged:
                merged[tv] = tp  # type: ignore
                continue
            prev_tp = merged[tv]
            if prev_tp == typing.Any:
                merged[tv] = tp  # type: ignore
            elif prev_tp == tp or tp == typing.Any:
                pass
            elif typing_inspect.is_typevar(prev_tp):
                merged[prev_tp] = merged[tv] = tp  # type: ignore
            elif typing_inspect.is_typevar(tp):
                merged[tp] = prev_tp  # type: ignore
            else:
                # Try merging them and choosing replacing the hint with the
                # merged values
                try:
                    merged[tv] = replace_typevars(  # type: ignore
                        match_types(prev_tp, tp), prev_tp
                    )
                    continue
                except TypeError:
                    pass
                try:
                    merged[tv] = replace_typevars(  # type: ignore
                        match_types(tp, prev_tp), tp
                    )
                    continue
                except TypeError:
                    pass
                raise TypeError(f"Cannot merge {prev_tp} and {tp} for type var {tv}")
    return merged


def get_inner_types(t: typing.Type) -> typing.Iterable[typing.Type]:
    """
    Returns the inner types for a type.

    Like `typing_inspect.get_args` but special cases callable, so it returns
    the return type, then all the arg types.
    """
    if t == typing.Callable:  # type: ignore
        return []
    if typing_inspect.get_origin(t) == collections.abc.Callable:
        arg_types, return_type = typing_inspect.get_args(t)
        return [return_type] + arg_types
    return typing_inspect.get_args(t)


def match_types(hint: typing.Type, t: typing.Type) -> TypeVarMapping:
    """
    Matches a type hint with a type, return a mapping of any type vars to their values.
    """
    # If it is an instance of OfType[Type[T]], then we should consider it as T
    if isinstance(t, OfType):
        of_type, = typing_inspect.get_args(get_type(t))
        assert issubclass(of_type, typing.Type)
        t, = typing_inspect.get_args(of_type)
        return match_types(hint, t)

    # If the type is an OfType[T] then we should really just consider it as T
    if issubclass(t, OfType) and not issubclass(hint, OfType):
        t, = typing_inspect.get_args(t)
        return match_types(hint, t)
    if issubclass(hint, OfType) and not issubclass(t, OfType):
        hint, = typing_inspect.get_args(hint)
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
    return merge_typevars(
        *(
            match_types(inner_hint, inner_t)
            for inner_hint, inner_t in zip(get_inner_types(hint), get_inner_types(t))
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

    # Special case empty callable, which raisees error on getting args
    if hint == typing.Callable:  # type: ignore
        return hint
    if typing_inspect.is_callable_type(hint):
        arg_types, return_type = typing_inspect.get_args(hint)
        return typing.Callable[
            [replace_typevars(typevars, a) for a in arg_types],
            replace_typevars(typevars, return_type),
        ]

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
    owner_origin: typing.Optional[typing.Type],
    is_classmethod: bool,
    args: typing.Tuple[object, ...],
    kwargs: typing.Mapping[str, object],
) -> typing.Tuple[
    typing.Tuple[object, ...],
    typing.Mapping[str, object],
    typing.Type[T],
    TypeVarMapping,
]:
    hints: typing.Dict[str, typing.Type] = typing.get_type_hints(fn)
    signature = inspect.signature(fn)

    mappings: typing.List[TypeVarMapping] = []
    # This case is triggered if we got here from a __get__ call
    # in a descriptor
    if owner:
        first_arg_name = next(iter(signature.parameters.keys()))
        first_arg_type: typing.Type
        if is_classmethod:
            # If we called this as a class method, add the owner to
            # the args add the inferred type to the hints.
            args = (owner,) + args  # type: ignore
            first_arg_type = typing.Type[owner_origin]  # type: ignore
        elif instance:
            # If we have called this as a method, then add the instance
            # to the args and infer the type hint for this first arg
            args = (instance,) + args
            first_arg_type = owner_origin  # type: ignore
        # we are calling an instance method on the class and passing the instance as the first arg
        else:
            # If the owner had type parameters set, we should use those to start computing variables
            # i.e. Class[int].__add__
            mappings.append(match_type(typing.Type[owner_origin], owner))
            first_arg_type = owner_origin  # type: ignore

        if first_arg_name not in hints:
            hints[first_arg_name] = first_arg_type  # type: ignore

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

    mappings += [match_type(hints[name], arg) for name, arg in argument_items]
    try:
        matches: TypeVarMapping = merge_typevars(*mappings)
    except ValueError:
        raise TypeError(f"Couldn't merge mappings {mappings}")

    return (
        # Remove first arg if it was a classmethod
        bound.args[1:] if is_classmethod else bound.args,
        bound.kwargs,
        replace_typevars(matches, return_hint),
        matches,
    )


WrapperType = typing.Callable[
    [
        typing.Callable[..., T],
        typing.Tuple[object, ...],
        typing.Mapping[str, object],
        typing.Type[T],
        TypeVarMapping,
    ],
    U,
]


@dataclasses.dataclass
class Infer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]

    def __post_init__(self):
        functools.update_wrapper(self, self.fn)
        self.__exposed__ = self

    def __call__(self, *args, **kwargs) -> U:
        return self.wrapper(  # type: ignore
            self, *infer_return_type(self.fn, None, None, None, False, args, kwargs)
        )

    def __get__(self, instance, owner) -> BoundInfer[T, U]:
        is_classmethod = isinstance(self.fn, classmethod)
        fn = self.fn.__func__ if is_classmethod else self.fn  # type: ignore
        return BoundInfer(  # type: ignore
            fn, self.wrapper, instance, owner, is_classmethod  # type: ignore
        )


@dataclasses.dataclass
class BoundInfer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U]
    instance: object
    owner: typing.Type
    is_classmethod: bool

    def __post_init__(self):
        functools.update_wrapper(self, self.fn)
        self._owner_origin = get_origin_type(self.owner)

        # Normalize this method so that equality checks on the returned function are consistant:
        # * Remove the instance, because it is already present in the args
        # * Replace the owner with the origin of the owner
        self.__exposed__ = (
            dataclasses.replace(self, instance=None, owner=self._owner_origin)
            if self.instance or self.owner != self._owner_origin
            else self
        )

    def __call__(self, *args, **kwargs) -> U:
        return self.wrapper(  # type: ignore
            self.__exposed__,
            *infer_return_type(
                self.fn,
                self.instance,
                self.owner,
                self._owner_origin,
                self.is_classmethod,
                args,
                kwargs,
            ),
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
    """

    return Infer(fn, wrapper)


def match_functions(
    fn_with_typevars: typing.Callable, fn: typing.Callable
) -> TypeVarMapping:
    if not isinstance(fn_with_typevars, BoundInfer) or not isinstance(fn, BoundInfer):
        if fn_with_typevars == fn:
            return {}
        raise TypeError(f"{fn_with_typevars} != {fn}")
    return match_types(fn_with_typevars.owner, fn.owner)


def replace_fn_typevars(
    fn: typing.Callable, typevars: TypeVarMapping
) -> typing.Callable:
    if isinstance(fn, BoundInfer):
        return dataclasses.replace(  # type: ignore
            fn, owner=replace_typevars(typevars, fn.owner)
        )
    return fn
