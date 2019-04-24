# import dataclasses
# import typing

# import pytest

# from .expressions import *
# from .instances import *

# T = typing.TypeVar("T", bound=Instance)


# @call(lambda a, b: a.__type__)
# def fn(a: T, b: T) -> T:
#     ...


# @call(lambda a: instance_type(Instance))
# def value_fn(a: int) -> Instance:
#     ...


# class InstanceSubclass(Instance):
#     pass


# @dataclasses.dataclass(frozen=True)
# class InstanceWithArg(Instance):
#     inner: InstanceType


# TEST_INSTANCES: typing.Iterable[Instance] = [
#     Instance(123),
#     fn(Instance(10), Instance(11)),
#     fn(InstanceSubclass(1), InstanceSubclass(2)),
#     InstanceWithArg(10, instance_type(Instance)),
#     InstanceWithArg(10, instance_type(InstanceWithArg, instance_type(Instance))),
#     Instance([1, 2, 3]),  # mutable value that doesn't have hash
#     value_fn(1),  # function with non instance arg
# ]


# @pytest.mark.parametrize("instance", TEST_INSTANCES)
# def test_instance_identity(instance) -> None:
#     """
#     You should be able to decompose any instances into it's type and expression and recompose it.
#     """
#     assert instance.__type__(instance.__expression__) == instance


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
