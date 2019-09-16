print("Importing")
from metadsl import *
from metadsl_core import *

print("Finished imports")


one = Integer.from_int(1)
zero = Integer.from_int(0)


@FunctionThree.from_fn_recursive
def fib_more(
    fn: FunctionThree[Integer, Integer, Integer, Integer],
    n: Integer,
    a: Integer,
    b: Integer,
) -> Integer:
    pred_cont = n > one
    minus1 = n - one
    ab = a + b
    added = fn(minus1, b, ab)

    n_eq_1 = n.eq(one)
    return pred_cont.if_(added, n_eq_1.if_(b, a))


@FunctionOne.from_fn
def fib(n: Integer) -> Integer:
    return fib_more(n, zero, one)


print("Starting execution")
print(execute(fib(Integer.from_int(10))))
