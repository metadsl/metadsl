from metadsl import execute
from .numpy_engine import *
import numpy
from .rules import *


def test_getitem():
    assert execute(ndarray_getitem(numpy.arange(10), 5)) == 5
