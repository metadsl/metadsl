from __future__ import annotations
from metadsl import *
from metadsl_core import *
from metadsl_rewrite import *

from .int_compat import *
from .tuple_compat import *
from .injest import *


item = IntCompat.from_maybe_integer(Maybe.just(Integer.from_int(0)))
tpl = HomoTupleCompat[IntCompat, Integer].from_maybe_vec(
    Maybe.just(Vec.create(Integer.from_int(0)))
)


def test_injest() -> None:
    assert execute(injest((0,))) == tpl
    # assert execute(injest(Integer.from_int(0))) == zero
    assert execute(injest(tpl)) == tpl


def test_getitem_int() -> None:
    assert execute(tpl[0]) == item
