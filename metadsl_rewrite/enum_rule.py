from __future__ import annotations

import inspect
from typing import Type

from metadsl import Expression
from metadsl.typing_tools import BoundInfer

from .rules import Rule
from .strategies import Strategy

__all__ = ["enum_rule"]


def enum_rule(cls: Type[Expression]) -> Strategy:
    """
    Defines a rule for a class that represents an enum, i.e. a constructor
    with some number of possible options. This is the same as a product type.

    Currently does not support any args for the different options, but that could be added
    if neccesary.

    Each value in the `match` method should match the name of a classmethod.

    >>> from typing import TypeVar, Generic
    >>> T = TypeVar("T")
    >>> class MyEnum(Expression, wrap_methods=True):
    ...     @classmethod
    ...     def one(cls) -> MyEnum:
    ...         ...
    ...     @classmethod
    ...     def two(cls) -> MyEnum:
    ...         ...
    ...
    ...     def match(self, one: T, two: T) -> T:
    ...         ...
    ...
    >>> from .strategies import Executor
    >>> execute = Executor(enum_rule(MyEnum))
    >>> execute(MyEnum.one().match(1, 2))
    1
    >>> execute(MyEnum.two().match(1, 2))
    2
    """
    # Fetch match function and verify that its signature is correct
    if not hasattr(cls, "match"):
        raise ValueError(f"{cls} must have create method")
    match_fn = cls.match  # type: ignore
    if not isinstance(match_fn, BoundInfer):
        raise ValueError(f"match method of {cls} must be an expression")
    if match_fn.is_classmethod:
        raise ValueError(f"match method of {cls} must not be a classmethod")
    fields = match_fn.__annotations__
    field_types = set(fields.values())
    if len(field_types) != 1:
        raise ValueError(
            f"match method of {cls} must have same types for args and return value"
        )
    field_type = field_types.pop()
    del field_types

    # Check that for each field there is a classmethod with the same name
    field_names = list(fields.keys())
    field_names.remove("return")
    del fields
    for field_name in field_names:
        if not hasattr(cls, field_name):
            raise ValueError(f"{cls} must have classmethod {field_name}")
        field_fn = getattr(cls, field_name)  # type: ignore
        if not isinstance(field_fn, BoundInfer):
            raise ValueError(f"{cls}.{field_name} must be an expression")
        if not field_fn.is_classmethod:
            raise ValueError(f"{cls}.{field_name} must be a classmethod")
        if field_fn.__annotations__ != {"return": cls.__qualname__}:
            raise ValueError(
                f"{cls}.{field_name} must not have any args and return the class"
            )

    def _match_fn(*args, field_names=field_names):
        for i, field_name in enumerate(field_names):
            yield getattr(cls, field_name)().match(*args), args[i]

    # Match function will take an arg for each field, with the generic param field_type
    _match_fn.__annotations__ = {field_name: field_type for field_name in field_names}
    _match_fn.__signature__ = inspect.Signature(  # type: ignore
        [
            inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=field_type,
            )
            for field_name in field_names
        ]
    )

    _match_fn.__module__ = cls.__module__
    _match_fn.__qualname__ = cls.__qualname__

    # Set __wrapped__ so that get_type_hints finds looks at the globals for this function
    _match_fn.__wrapped__ = match_fn.fn  # type: ignore
    return Rule(_match_fn)
