from metadsl_all import *

N = 11
print(execute(Converter[Vec[Integer]].convert(tuple(range(N)))))
