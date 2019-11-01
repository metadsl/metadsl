from __future__ import annotations


from metadsl import *
from .conversion import *
from .either import *
from .abstraction import *
from .rules import all_rules
from .maybe import *


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


IntStr = Either[Int, Str]


class TestMatches:
    def test_matches(self):
        @Abstraction.from_fn
        def double_int(i: Int) -> Int:
            return Int.from_int(2) * i

        str_to_int = Abstraction.from_fn(Int.from_str)

        assert execute(
            IntStr.left(Int.from_int(10)).match(double_int, str_to_int)
        ) == Int.from_int(2) * Int.from_int(10)

        assert execute(
            IntStr.right(Str.from_str("10")).match(double_int, str_to_int)
        ) == Int.from_str(Str.from_str("10"))


@rule
def convert_to_int(i: int) -> R[Maybe[Int]]:
    return Converter[Int].convert(i), lambda: Maybe.just(Int.from_int(i))


@rule
def convert_to_str(s: str) -> R[Maybe[Str]]:
    return Converter[Str].convert(s), lambda: Maybe.just(Str.from_str(s))


convert_rules = RulesRepeatFold(convert_to_str, convert_to_int, all_rules)


class TestConvert:
    def test_convert_int(self):
        assert execute(Converter[Int].convert(123), convert_rules) == Maybe.just(
            Int.from_int(123)
        )

    def test_convert_str(self):
        assert execute(Converter[Str].convert("hi"), convert_rules) == Maybe.just(
            Str.from_str("hi")
        )

    def test_convert_either_int(self):
        assert execute(Converter[IntStr].convert(123), convert_rules) == Maybe.just(
            IntStr.left(Int.from_int(123))
        )

    def test_convert_either_str(self):
        assert execute(Converter[IntStr].convert("hi"), convert_rules) == Maybe.just(
            IntStr.right(Str.from_str("hi"))
        )
