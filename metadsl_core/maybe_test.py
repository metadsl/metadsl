from __future__ import annotations


from metadsl import *
from .abstraction import *
from .maybe import *


class Int(Expression):
    @expression
    def __mul__(self, other: Int) -> Int:
        ...

    @expression
    @classmethod
    def from_int(cls, i: int) -> Int:
        ...


class TestMaybe:
    def test_matches(self):
        @Abstraction.from_fn
        def double_int(i: Int) -> Int:
            return Int.from_int(2) * i

        assert execute(
            Maybe.just(Int.from_int(10)).match(Int.from_int(5), double_int)
        ) == Int.from_int(2) * Int.from_int(10)
        assert execute(
            Maybe[Int].nothing().match(Int.from_int(5), double_int)
        ) == Int.from_int(5)

    def test_map(self):
        @Abstraction.from_fn
        def double_int(i: Int) -> Int:
            return Int.from_int(2) * i

        assert execute(Maybe.just(Int.from_int(10)).map(double_int)) == Maybe[Int].just(
            Int.from_int(2) * Int.from_int(10)
        )
        assert execute(Maybe[Int].nothing().map(double_int)) == Maybe[Int].nothing()
