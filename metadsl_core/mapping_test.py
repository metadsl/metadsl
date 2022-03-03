from __future__ import annotations


from metadsl import *
from metadsl_rewrite import *
from .mapping import *



def test_getitem_first():
    e = Mapping[str, int].empty()
    assert execute(e.setitem("h", 1)["h"]) == 1

def test_getitem_nested():
    e = Mapping[str, int].empty()
    assert execute(e.setitem("h", 1).setitem("j", 10)["h"]) == 1