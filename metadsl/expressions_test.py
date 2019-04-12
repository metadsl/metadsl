from .expressions import *
import typing
import dataclasses
import pytest

T = typing.TypeVar("T", bound=Instance)


@call(lambda a, b: a)
def fn(a: T, b: T) -> T:
    ...


class InstanceSubclass(Instance):
    pass


@dataclasses.dataclass(frozen=True)
class InstanceWithArg(Instance):
    inner: InstanceType


TEST_INSTANCES: typing.Iterable[Instance] = [
    Instance(123),
    fn(Instance(10), Instance(11)),
    fn(InstanceSubclass(1), InstanceSubclass(2)),
    InstanceWithArg(10, instance_type(Instance)),
    InstanceWithArg(10, instance_type(InstanceWithArg, instance_type(Instance))),
]


@pytest.mark.parametrize("instance", TEST_INSTANCES)
def test_instance_to_expression(instance) -> None:
    """
    You should be able to translate from instances to expressions and back again,
    preserving equality.
    """
    assert Expression.from_instance(instance).instance == instance


TEST_VALUES = [10]


@pytest.mark.parametrize("value", TEST_VALUES)
def test_compact(value) -> None:
    """
    If you call compact on an instance, leaves that have the same hash should be
    replaced with one instance.
    """
    left = Instance(value)
    right = Instance(value)
    total = fn(left, right)
    compacted = Expression.from_instance(total).compact()
    assert compacted.instance == total
    left_new, right_new = compacted.value.args
    assert left_new is right_new
