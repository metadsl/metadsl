from __future__ import annotations


from metadsl import *
from .conversion import *
from .either import *
from .abstraction import *
from .rules import *
from .maybe import *
from .vec import *


class Int(Expression):
    @expression
    @classmethod
    def from_int(cls, i: int) -> Int:
        ...


class Str(Expression):
    @expression
    @classmethod
    def from_str(cls, s: str) -> Str:
        ...


@rule
def convert_to_int(i: int, s: str) -> R[Maybe[Int]]:
    yield Converter[Int].convert(i), lambda: Maybe.just(Int.from_int(i))
    yield Converter[Int].convert(s), Maybe[Int].nothing()


@rule
def convert_to_str(i: int, s: str) -> R[Maybe[Str]]:
    yield Converter[Str].convert(s), lambda: Maybe.just(Str.from_str(s))
    yield Converter[Str].convert(i), Maybe[Str].nothing()


convert_rules = RulesRepeatFold(convert_to_str, convert_to_int, *core_rules.rules)

e = lambda e: execute_rule(convert_rules, e)


class TestConvert:
    def test_convert_empty(self):
        assert e(Converter[Vec[Int]].convert(())) == Maybe.just(Vec[Int].create())

    def test_convert_items(self):
        assert e(Converter[Vec[Int]].convert((1, 2))) == Maybe.just(
            Vec.create(Int.from_int(1), Int.from_int(2))
        )

    def test_invalid_conversion(self):
        assert e(Converter[Vec[Int]].convert((1, "hi"))) == Maybe[Vec[Int]].nothing()
        assert e(Converter[Vec[Int]].convert(("hi", 1))) == Maybe[Vec[Int]].nothing()
        assert e(Converter[Vec[Int]].convert(("hi",))) == Maybe[Vec[Int]].nothing()
