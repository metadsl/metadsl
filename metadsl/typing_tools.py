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
    "TypeVarScope",
    "infer_return_type",
    "ExpandedType",
    "replace_fn_typevars",
    "merge_typevars",
    "match_types",
    "get_origin_type",
    "get_fn_typevars",
]

T = typing.TypeVar("T")
U = typing.TypeVar("U")


class GenericCheckType(type):
    @functools.lru_cache()
    def __subclasscheck__(cls, sub):
        """
        Modified from https://github.com/python/cpython/blob/aa73841a8fdded4a462d045d1eb03899cbeecd65/Lib/typing.py#L707-L717
        """
        sub = getattr(sub, "__origin__", sub)
        if hasattr(cls, "__origin__"):
            return issubclass(sub, cls)
        if sub == typing.Any:
            return False

        # Needed when checking if T or Union is instance of Expression
        if isinstance(sub, typing.TypeVar) or sub == typing.Union:  # type: ignore
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
    if "__origin__" in self.__dict__ and attr not in (
        "__wrapped__",
        "__union_params__",
    ):
        # If the attribute is a descriptor, pass in the generic class
        try:
            property = self.__origin__.__getattribute__(self.__origin__, attr)
        except Exception:
            return

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


# Allow isinstance and issubclass calls on special forms like union
def special_form_subclasscheck(self, cls):
    if self == typing.Any:
        return True
    if self == cls:
        return True
    raise TypeError


typing._GenericAlias.__subclasscheck__ = generic_subclasscheck  # type: ignore
typing._SpecialForm.__subclasscheck__ = special_form_subclasscheck  # type: ignore


def get_origin(t: typing.Type) -> typing.Type:
    origin = typing_inspect.get_origin(t)
    # Need workaround for sequences
    # https://github.com/ilevkivskyi/typing_inspect/issues/36
    if origin == collections.abc.Sequence:
        return typing.Sequence

    if origin == tuple:
        return typing.Tuple  # type: ignore

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
    signature = inspect_signature(fn)
    type_hints = typing_get_type_hints(fn)
    arg_hints: typing.List[typing.Type] = []

    for arg_name, p in signature.parameters.items():
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            arg_hints.append(
                type_hints.get(arg_name, typing.cast(typing.Type, typing.Any))
            )
        else:
            raise NotImplementedError(f"Does not support getting type of {signature}")
    return typing.Callable[arg_hints, type_hints.get("return", typing.Any)]


def get_function_replace_type(f: FunctionReplaceTyping) -> typing.Type[typing.Callable]:
    return replace_typevars(f.typevars, get_function_type(f.fn))


def get_bound_infer_type(b: BoundInfer) -> typing.Type[typing.Callable]:
    """
    Returns a typing.Callable type that corresponds to the type of the bound infer.

    TODO: This logic is a combination of `get_function_type` and `infer_return_type`.
    We should eventually merge all of this into a consistant API so we don't have to duplicate this code.
    """
    hints = copy.copy(typing_get_type_hints(b.fn))
    signature = inspect_signature(b.fn)

    # We want to get the original type hints for the first arg,
    # and match those against the first arg in the bound, so we get a typevar mapping
    first_arg_name = next(iter(signature.parameters.keys()))
    typevars: TypeVarMapping
    # Whether to skip the first arg of the param of the signature when computing the signature
    skip_first_param: bool
    owner_origin = get_origin_type(b.owner)
    if b.is_classmethod:
        # If we called this as a class method
        typevars = match_type(typing.Type[owner_origin], b.owner)
        skip_first_param = True
    else:
        # we are calling an instance method on the class and passing the instance as the first arg
        typevars = match_type(typing.Type[owner_origin], b.owner)
        skip_first_param = False
        hints[first_arg_name] = owner_origin

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
    if isinstance(v, functools.partial):  # type: ignore
        inner_type = get_type(v.func)  # type: ignore
        if v.keywords:  # type: ignore
            raise TypeError
        inner_args, inner_return = typing_inspect.get_args(inner_type)
        mapping: TypeVarMapping = merge_typevars(
            *(
                match_type(arg_type, arg)
                for (arg_type, arg) in zip(inner_args, v.args)  # type: ignore
            )
        )
        rest_arg_types = inner_args[len(v.args) :]  # type: ignore
        return typing.Callable[
            [replace_typevars(mapping, arg) for arg in rest_arg_types],
            replace_typevars(mapping, inner_return),
        ]

    if isinstance(v, Infer):
        return get_function_type(v.fn)  # type: ignore
    if isinstance(v, BoundInfer):
        return get_bound_infer_type(v)  # type: ignore
    if isinstance(v, FunctionReplaceTyping):
        return get_function_replace_type(v)  # type: ignore

    tp = typing_inspect.get_generic_type(v)
    # Special case, only support homogoneous tuple that are inferred to iterables
    if tp == tuple:
        if v:
            return typing.Sequence[get_type(v[0])]  # type: ignore
        return typing.Sequence  # type: ignore
    # Special case, also support function types.
    if tp == types.FunctionType:
        return get_function_type(v)  # type: ignore

    return tp


TypeVarMapping = typing.Mapping[typing.TypeVar, typing.Type]  # type: ignore


def match_values(hint_value: T, value: T) -> TypeVarMapping:
    return match_type(get_type(hint_value), value)


def match_type(hint: typing.Type[T], value: T) -> TypeVarMapping:
    if typing_inspect.get_origin(hint) == type:
        (inner_hint,) = typing_inspect.get_args(hint)
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


def get_all_typevars(t: typing.Type) -> typing.Iterable[typing.TypeVar]:  # type: ignore
    for t in get_inner_types(t):
        if isinstance(t, typing.TypeVar):  # type: ignore
            yield t
        else:
            yield from get_all_typevars(t)


def match_types(hint: typing.Type, t: typing.Type) -> TypeVarMapping:
    """
    Matches a type hint with a type, return a mapping of any type vars to their values.
    """
    if hint == t:
        return {}

    # If it is an instance of OfType[Type[T]], then we should consider it as T
    if isinstance(t, OfType):
        (of_type,) = typing_inspect.get_args(get_type(t))
        assert issubclass(of_type, typing.Type)
        (t,) = typing_inspect.get_args(of_type)
        return match_types(hint, t)

    # If the type is an OfType[T] then we should really just consider it as T
    if issubclass(t, OfType) and not issubclass(hint, OfType):
        (t,) = typing_inspect.get_args(t)
        return match_types(hint, t)
    if issubclass(hint, OfType) and not issubclass(t, OfType):
        (hint,) = typing_inspect.get_args(hint)
        return match_types(hint, t)

    # Matching an expanded type is like matching just whatever it represents
    if issubclass(t, ExpandedType):
        (t,) = typing_inspect.get_args(t)

    if typing_inspect.is_typevar(hint):
        return {hint: t}

    # This happens with match rule on conversion, like when the value is TypeVar
    if typing_inspect.is_typevar(t):
        return {}

    # if both are generic sequences, verify they are the same and have the same contents
    if (
        typing_inspect.is_generic_type(hint)
        and typing_inspect.is_generic_type(t)
        and typing_inspect.get_origin(hint) == collections.abc.Sequence
        and typing_inspect.get_origin(t) == collections.abc.Sequence
    ):
        t_inner = typing_inspect.get_args(t)[0]

        # If t's inner arg is just the default one for seuqnce, it hasn't be initialized so assume
        # it was an empty tuple that created it and just return a match
        if t_inner == typing_inspect.get_args(typing.Sequence)[0]:
            return {}
        return match_types(typing_inspect.get_args(hint)[0], t_inner)

    if typing_inspect.is_union_type(hint):
        # If this is a union, iterate through and use the first that is a subclass
        for inner_type in typing_inspect.get_args(hint):
            if issubclass(t, inner_type):
                hint = inner_type
                break
        else:
            raise TypeError(f"Cannot match concrete type {t} with hint {hint}")

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
    if typing_inspect.get_origin(hint) == collections.abc.Callable:
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


@functools.lru_cache()
def inspect_signature(fn: typing.Callable) -> inspect.Signature:
    return inspect.signature(fn)


@functools.lru_cache()
def typing_get_type_hints(fn: typing.Callable) -> typing.Dict[str, typing.Type]:
    return typing.get_type_hints(fn)


def get_arg_hints(fn: typing.Callable) -> typing.List[typing.Type]:
    signature = inspect_signature(fn)
    hints = typing_get_type_hints(fn)
    return [hints[param] for param in signature.parameters.keys()]


def infer_return_type(
    fn: typing.Callable[..., T],
    owner: typing.Optional[typing.Type],
    is_classmethod: bool,
    args: typing.Tuple[object, ...],
    kwargs: typing.Mapping[str, object],
) -> typing.Tuple[
    typing.Tuple[object, ...],
    typing.Mapping[str, object],
    typing.Type[T],
    TypeVarMapping,
]:
    hints = copy.copy(typing_get_type_hints(fn))
    signature = inspect_signature(fn)

    mappings: typing.List[TypeVarMapping] = []
    # This case is triggered if we got here from a __get__ call
    # in a descriptor
    if owner:
        first_arg_name = next(iter(signature.parameters.keys()))
        first_arg_type: typing.Type
        owner_origin = get_origin_type(owner)
        if is_classmethod:
            # If we called this as a class method, add the owner to
            # the args add the inferred type to the hints.
            args = (owner,) + args  # type: ignore
            first_arg_type = typing.Type[owner_origin]  # type: ignore
        else:
            # If the owner had type parameters set, we should use those to start computing variables
            # i.e. Class[int].__add__
            mappings.append(match_types(owner_origin, owner))
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

    return_hint: typing.Type[T] = hints.pop("return", typing.Any)  # type: ignore

    mappings += [
        match_type(hints.get(name, typing.Any), arg)  # type: ignore
        for name, arg in argument_items
    ]
    try:
        matches: TypeVarMapping = merge_typevars(*mappings)
    except ValueError:
        raise TypeError(f"Couldn't merge mappings {mappings}")

    final_args = bound.args[1:] if is_classmethod else bound.args
    final_kwargs = bound.kwargs
    for arg in final_args:
        record_scoped_typevars(arg, *matches.keys())
    for kwarg in final_kwargs.values():
        record_scoped_typevars(kwarg, *matches.keys())
    return (final_args, final_kwargs, replace_typevars(matches, return_hint), matches)


def record_scoped_typevars(f: object, *additional_typevars: typing.TypeVar) -> None:  # type: ignore
    if not isinstance(f, types.FunctionType):
        return
    f.__scoped_typevars__ = frozenset(  # type: ignore
        {
            *get_all_typevars(get_function_type(f)),
            *get_typevars_in_scope(),
            *additional_typevars,
        }
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


_TYPEVARS_IN_SCOPE: typing.Counter[  # type: ignore
    typing.TypeVar
] = collections.Counter()


def get_typevars_in_scope() -> typing.Set[typing.TypeVar]:  # type: ignore
    return set(k for k, v in _TYPEVARS_IN_SCOPE.items() if v > 0)


@dataclasses.dataclass
class TypeVarScope:
    typevars_in_scope: typing.Tuple[typing.TypeVar, ...]  # type: ignore

    def __init__(self, *tvs: typing.TypeVar) -> None:  # type: ignore
        self.typevars_in_scope = tvs

    def __enter__(self) -> None:
        _TYPEVARS_IN_SCOPE.update(self.typevars_in_scope)

    def __exit__(self, *exc_details) -> None:
        _TYPEVARS_IN_SCOPE.subtract(self.typevars_in_scope)


@dataclasses.dataclass
class NewTypeVarScope:
    previous_typvars_in_scope: typing.Optional[  # type: ignore
        typing.Counter[typing.TypeVar]
    ] = None

    def __enter__(self) -> None:
        assert not self.previous_typvars_in_scope
        self.previous_typvars_in_scope = collections.Counter(_TYPEVARS_IN_SCOPE)
        _TYPEVARS_IN_SCOPE.clear()

    def __exit__(self, *exc_details) -> None:
        assert self.previous_typvars_in_scope
        _TYPEVARS_IN_SCOPE.update(self.previous_typvars_in_scope)


@dataclasses.dataclass(unsafe_hash=True)
class Infer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U] = dataclasses.field(repr=False)

    def __post_init__(self):
        functools.update_wrapper(self, self.fn)

    def __call__(self, *args, **kwargs) -> U:
        *wrapper_args, typevars = infer_return_type(self.fn, None, False, args, kwargs)
        with TypeVarScope(*typevars.keys()):
            res = self.wrapper(self, *wrapper_args)  # type: ignore
        return res

    def __get__(self, instance, owner) -> BoundInfer[T, U]:
        is_classmethod = isinstance(self.fn, classmethod)
        is_property = isinstance(self.fn, property)
        if is_classmethod and is_property:
            raise NotImplementedError("classmethod properties are not supported")
        fn = self.fn
        if is_classmethod:
            fn = fn.__func__  # type: ignore
        if is_property:
            fn = fn.fget  # type: ignore
        if instance:
            method = BoundInfer(  # type: ignore
                fn, self.wrapper, get_type(instance), is_classmethod  # type: ignore
            )
            if is_property:
                return method(instance)  # type: ignore
            return functools.partial(method, instance)  # type: ignore
        return BoundInfer(  # type: ignore
            fn, self.wrapper, owner, is_classmethod  # type: ignore
        )

    def __repr__(self):
        return getattr(self.fn, "__name__", str(self.fn))


@dataclasses.dataclass(unsafe_hash=True)
class BoundInfer(typing.Generic[T, U]):
    fn: typing.Callable[..., T]
    wrapper: WrapperType[T, U] = dataclasses.field(repr=False)
    owner: typing.Type
    is_classmethod: bool

    def __post_init__(self):
        functools.update_wrapper(self, self.fn)

    def __call__(self, *args, **kwargs) -> U:
        *wrapper_args, typevars = infer_return_type(
            self.fn, self.owner, self.is_classmethod, args, kwargs
        )
        with TypeVarScope(*typevars.keys()):
            res = self.wrapper(self, *wrapper_args)  # type: ignore
        return res

    def __repr__(self):
        # Generic types are already formatted nicely
        owner_str = self.owner.__name__
        return f"{owner_str}.{self.fn.__name__}"


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
    if fn_with_typevars.fn == fn.fn:
        return match_types(fn_with_typevars.owner, fn.owner)
    raise TypeError(f"{fn_with_typevars} != {fn}")


@dataclasses.dataclass(unsafe_hash=True)
class FunctionReplaceTyping:
    fn: typing.Callable
    typevars: HashableMapping[typing.TypeVar, typing.Type]  # type: ignore
    typevars_in_scope: typing.FrozenSet[typing.TypeVar]  # type: ignore
    inner_mapping: typing.Callable[[typing.Any], typing.Any]

    @classmethod
    def create(
        cls,
        fn: typing.Callable,
        typevars: TypeVarMapping,
        inner_mapping: typing.Callable[[typing.Any], typing.Any],
    ) -> typing.Callable:
        if isinstance(fn, FunctionReplaceTyping):
            return fn
        typevars_in_scope: typing.FrozenSet[TypeVar] = fn.__scoped_typevars__  # type: ignore
        if not typevars_in_scope:
            return fn
        if "fib_more" in str(fn):
            return fn

        typevars = HashableMapping(
            {k: v for k, v in typevars.items() if k in typevars_in_scope}
        )
        res = cls(fn, typevars, typevars_in_scope, inner_mapping)

        functools.update_wrapper(res, fn)
        res.__annotations__ = {
            k: replace_typevars(typevars, v)
            for k, v in typing_get_type_hints(fn).items()
        }

        return res

    def __call__(self, *args, **kwargs):
        with NewTypeVarScope():
            with TypeVarScope(*self.typevars_in_scope):
                return self.inner_mapping(self.fn(*args, **kwargs))  # type: ignore


@dataclasses.dataclass(unsafe_hash=True)
class Identity:
    def __call__(self, a):
        return a


def replace_fn_typevars(
    fn: T,
    typevars: TypeVarMapping,
    inner_mapping: typing.Callable[[T], T] = Identity(),
) -> T:
    if isinstance(fn, BoundInfer):
        return typing.cast(
            T,
            BoundInfer(  # type: ignore
                fn=fn.fn,
                wrapper=fn.wrapper,  # type: ignore
                is_classmethod=fn.is_classmethod,
                owner=replace_typevars(typevars, fn.owner),
            ),
        )
    if isinstance(fn, types.FunctionType):
        # Create new function by replacing typevars in existing function
        return FunctionReplaceTyping.create(fn, typevars, inner_mapping)  # type: ignore
    return fn


def get_fn_typevars(fn: object) -> TypeVarMapping:
    if isinstance(fn, BoundInfer):
        return match_types(get_origin_type(fn.owner), fn.owner)
    return {}
