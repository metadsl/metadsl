from __future__ import annotations


from metadsl import *
from .conversion import *
from .either import *
from .abstraction import *
from .rules import core_rules


class Int(Expression):
    @expression
    def __mul__(self, other: Int) -> Int:
        ...

    @expression
    @classmethod
    def from_str(cls, str: Str) -> Int:
        ...

    @expression
    @classmethod
    def from_int(cls, i: int) -> Int:
        ...


class Str(Expression):
    @expression
    @classmethod
    def from_str(cls, s: str) -> Str:
        ...


class TestEither:
    def test_matches(self):
        @Abstraction.from_fn
        def double_int(i: Int) -> Int:
            return Int.from_int(2) * i

        str_to_int = Abstraction.from_fn(Int.from_str)

        assert execute_rule(
            core_rules,
            Either[Int, Str].left(Int.from_int(10)).match(double_int, str_to_int),
        ) == Int.from_int(2) * Int.from_int(10)

        assert execute_rule(
            core_rules,
            Either[Int, Str].right(Str.from_str("10")).match(double_int, str_to_int),
        ) == Int.from_str(Str.from_str("10"))
