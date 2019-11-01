from metadsl import *
from metadsl_core import *


N = 11
print(execute(Converter[Vec[Integer]].convert(tuple(range(N)))))
