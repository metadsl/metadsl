from __future__ import annotations
from metadsl import *
from metadsl_core import *

from .bool_compat import *
from .injest import *


def test_if_bool() -> None:
    assert execute(if_guess(True, True, False)) == execute(injest(True))
    assert execute(if_guess(False, True, False)) == execute(injest(False))
