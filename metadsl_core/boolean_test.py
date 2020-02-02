from __future__ import annotations


from metadsl import *
from .boolean import *


class TestBoolean:
    def test_if(self):
        assert execute(Boolean.create(True).if_(0, 1)) == 0
        assert execute(Boolean.create(False).if_(0, 1)) == 1
