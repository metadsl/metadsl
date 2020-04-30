from __future__ import annotations
from metadsl import *
from metadsl_core import *
from metadsl_rewrite import *

from .bool_compat import *
from .injest import *


t = BoolCompat.from_maybe_boolean(Maybe.just(Boolean.create(True)))
f = BoolCompat.from_maybe_boolean(Maybe.just(Boolean.create(False)))


def test_injest() -> None:
    assert execute(injest(True)) == t
    assert execute(injest(Boolean.create(True))) == t
    assert execute(injest(t)) == t


def test_if_bool() -> None:
    assert execute(t.if_(True, False)) == t
    assert execute(f.if_(True, False)) == f
