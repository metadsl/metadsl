from __future__ import annotations
from metadsl import *
from metadsl_core import *

from .bool_compat import *
from .injest import *


t: BoolCompat = injest(True)
f: BoolCompat = injest(False)


def test_if_bool() -> None:
    assert execute(t.if_(True, False)) == execute(injest(True))
    assert execute(f.if_(True, False)) == execute(injest(False))
