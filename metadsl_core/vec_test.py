from __future__ import annotations
import pytest

from metadsl import *
from metadsl_rewrite import *

from .conversion import *
from .either import *
from .abstraction import *
from .strategies import *
from .maybe import *
from .vec import *
from .integer import *


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


vec_convert = register.tmp(convert_to_str, convert_to_int)


class TestVec:
    def test_getitem(self):
        assert execute(Vec.create(10, 11)[Integer.from_int(1)]) == 11

    def test_append(self):
        assert execute(Vec.create(10).append(11)) == Vec.create(10, 11)

    @vec_convert
    def test_convert_empty(self):
        assert execute(Converter[Vec[Int]].convert(())) == Maybe.just(Vec[Int].create())

    @vec_convert
    def test_convert_items(self):
        assert execute(Converter[Vec[Int]].convert((1, 2))) == Maybe.just(
            Vec.create(Int.from_int(1), Int.from_int(2))
        )

    @vec_convert
    def test_invalid_conversion(self):
        assert (
            execute(Converter[Vec[Int]].convert((1, "hi"))) == Maybe[Vec[Int]].nothing()
        )
        assert (
            execute(Converter[Vec[Int]].convert(("hi", 1))) == Maybe[Vec[Int]].nothing()
        )
        assert (
            execute(Converter[Vec[Int]].convert(("hi",))) == Maybe[Vec[Int]].nothing()
        )
