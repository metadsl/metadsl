from __future__ import annotations
from metadsl import *
from metadsl_core import *
from metadsl_rewrite import *

from .int_compat import *
from .injest import *


zero = IntCompat.from_maybe_integer(Maybe.just(Integer.from_int(0)))
one = IntCompat.from_maybe_integer(Maybe.just(Integer.from_int(1)))


def test_injest() -> None:
    assert execute(injest(0)) == zero
    assert execute(injest(Integer.from_int(0))) == zero
    assert execute(injest(zero)) == zero


def test_add() -> None:
    assert execute(zero + 1) == one


def test_radd() -> None:
    assert execute(1 + zero) == one
