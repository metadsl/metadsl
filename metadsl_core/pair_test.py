from __future__ import annotations

from metadsl import *

from .integer import *
from .pair import *


class TestPair:
    def test_left(self):
        assert execute(Pair.create(1, 2).left) == 1

    def test_right(self):
        assert execute(Pair.create(1, 2).right) == 2

    def test_left_type(self):
        assert execute(
            Pair.create(Integer.from_int(1), 2).left + Integer.from_int(1)
        ) == Integer.from_int(2)
