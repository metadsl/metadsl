import dataclasses
import typing

import pytest

from .calls import *
from .expressions import *

T = typing.TypeVar("T", bound=Instance)


@call(lambda a, b: type(a))
def fn(a: T, b: T) -> T:
    ...


@call(lambda a: Instance)
def value_fn(a: int) -> Instance:
    ...


class InstanceSubclass(Instance):
    pass


@call(lambda a: InstanceSubclass)
def subclass_fn(a: int) -> InstanceSubclass:
    ...


@dataclasses.dataclass
class InstanceWithArg(Instance):
    inner: typing.Callable[[typing.Any], Instance]


@call(lambda a, t: (lambda x: InstanceWithArg(x, t)))
def instance_arg_fn(
    a: int, t: typing.Callable[[typing.Any], Instance]
) -> InstanceWithArg:
    ...


@call(lambda a: Instance)
def mutable_fn(a: typing.List) -> Instance:
    ...


TEST_INSTANCES: typing.Iterable[Instance] = [
    value_fn(123),
    fn(value_fn(10), value_fn(11)),
    fn(subclass_fn(1), subclass_fn(2)),
    instance_arg_fn(10, Instance),
    instance_arg_fn(10, lambda x: InstanceWithArg(x, Instance)),
    mutable_fn([1, 2, 3]),  # mutable value that doesn't have hash
]


@pytest.mark.parametrize("instance", TEST_INSTANCES)
def test_instance_identity(instance) -> None:
    """
    You should be able to decompose any instances into it's type and expression and recompose it.
    """
    assert from_expression(to_expression(instance)) == instance


# We aren't memoizing for now

# TEST_VALUES = [10, []]


# @pytest.mark.parametrize("value", TEST_VALUES)
# def test_memoized(value) -> None:
#     """
#     If you call compact on an instance, leaves that have the same hash, should be
#     replaced with one instance.
#     """
#     left = Instance(value)
#     right = Instance(value)
#     total = fn(left, right)
#     compacted = Expression.from_instance(total).compact()
#     assert compacted.instance == total
#     left_new, right_new = compacted.value.args
#     assert left_new is right_new
