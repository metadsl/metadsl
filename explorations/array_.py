from __future__ import annotations
import typing

from metadsl import *
from metadsl_core import *

import metadsl_visualize

T = typing.TypeVar("T")
Shape = Vec[Integer]
Indices = Vec[Integer]


class Array(Expression, typing.Generic[T]):
    @expression
    @classmethod
    def create(cls, shape: Shape, index_fn: Abstraction[Indices, T]) -> Array[T]:
        ...

    @expression
    def __matmul__(self, other: Array[T]) -> Array[T]:
        ...

    @expression
    @classmethod
    def range(cls, length: Integer) -> Array[Integer]:
        ...

    @expression
    def __add__(self, other: Array[T]) -> Array[T]:
        ...

    @expression
    def transpose(self) -> Array[T]:
        ...


@register
@rule
def _transpose(shape: Shape, idx: Abstraction[Indices, T]) -> R[Array[T]]:
    dims = shape.length
    result_shape = shape.drop(Integer.from_int(1)).append(shape[Integer.from_int(0)])

    @Abstraction.from_fn
    def result_idx(indices: Indices) -> T:
        # take last of index vector and pass to front
        last_index = indices[dims]
        rest_indices = indices.take(dims - Integer.from_int(1))

        return idx(Vec.create(last_index) + rest_indices)

    return Array.create(shape, idx).transpose(), Array.create(result_shape, result_idx)


@register
@rule
def _outer_product(
    l_shape: Shape,
    r_shape: Shape,
    l_idx: Abstraction[Indices, Integer],
    r_idx: Abstraction[Indices, Integer],
):
    l_size = l_shape.length

    @Abstraction.from_fn
    def index_fn(indices: Indices) -> Integer:
        return l_idx(indices.take(l_size)) * r_idx(indices.drop(l_size))

    return (
        Array.create(l_shape, l_idx) @ Array.create(r_shape, r_idx),
        Array.create(l_shape + r_shape, index_fn),
    )


@register
@rule
def _add_integer(
    l_shape: Shape,
    r_shape: Shape,
    l_idx: Abstraction[Indices, Integer],
    r_idx: Abstraction[Indices, Integer],
):
    @Abstraction.from_fn
    def index_fn(indices: Indices) -> Integer:
        return l_idx(indices) + r_idx(indices)

    return (
        Array.create(l_shape, l_idx) + Array.create(r_shape, r_idx),
        Array.create(l_shape, index_fn),
    )


@register
@rule
def _range_create(length: Integer):
    @Abstraction.from_fn
    def index_fn(indices: Indices) -> Integer:
        return indices[Integer.from_int(0)]

    return (Array.range(length), Array.create(Shape.create(length), index_fn))


python_string_rules = RulesRepeatFold()

rule_groups["python_string"] = python_string_rules
register_python_string = python_string_rules.append


@expression
def concat(l: str, r: str) -> str:
    ...


@register
@rule
def _concat_rule(l: str, r: str):
    return concat(l, r), lambda: l + r


@expression
def python_string_integer(s: str) -> Integer:
    ...


@expression
def integer_python_string(i: Integer) -> str:
    ...


@register
@rule
def _python_string_integer_rule(s: str):
    return integer_python_string(python_string_integer(s)), s


@expression
def python_string_shape(s: str) -> Shape:
    ...


@expression
def shape_python_string(s: Shape) -> str:
    ...


@register
@rule
def _vec_add_str(l: str, r: str):
    return (
        python_string_shape(l) + python_string_shape(r),
        lambda: python_string_shape(f"({l} + {r})"),
    )


@register
@rule
def _python_string_shape_rule(s: str):
    return shape_python_string(python_string_shape(s)), s


@expression
def python_string_array(s: str) -> Array[Integer]:
    ...


@expression
def array_python_string(a: Array[Integer]) -> str:
    ...


@register
@rule
def _python_string_array_rule(s: str):
    return array_python_string(python_string_array(s)), s


# @register_python_string
# @rule
# def _to_array_three(i: str, j: str, k: str, index_fn: Abstraction[Indices, Integer]):
#     def result():
#         return python_string_array(
#             concat(
#                 f"""
# shape = ({i}, {j}, {k})
# array = np.empty(shape)
# for i_ in range(shape[0]):
#     for j_ in range(shape[1]):
#         for k_ in range(shape[2]):
#             array[i_, j_, k_] = """,
#                 integer_python_string(
#                     index_fn(
#                         Vec.create(
#                             python_string_integer("i_"),
#                             python_string_integer("j_"),
#                             python_string_integer("k_"),
#                         )
#                     )
#                 ),
#             )
#         )

#     return (
#         Array.create(
#             Vec.create(
#                 python_string_integer(i),
#                 python_string_integer(j),
#                 python_string_integer(k),
#             ),
#             index_fn,
#         ),
#         result,
#     )


@register_python_string
@rule
def _to_vec_fn(l: str, index_fn: Abstraction[Integer, Integer]) -> R[Vec[Integer]]:
    def result() -> Vec[Integer]:
        return python_string_shape(
            concat(
                concat(
                    "[", integer_python_string(index_fn(python_string_integer("i"))),
                ),
                f"for i in range({l})]",
            )
        )

    return Vec.create_fn(python_string_integer(l), index_fn), result


@register_python_string
@rule
def _to_array(shape: str, index_fn: Abstraction[Indices, Integer]):
    def result():
        return python_string_array(
            concat(
                f"""
shape = {shape}
array = np.empty(shape)
for indices in itertools.product(*map(range, shape)):
    array[indices] = """,
                integer_python_string(index_fn(python_string_shape("indices"))),
            )
        )

    return Array.create(python_string_shape(shape), index_fn), result


@register_python_string
@rule
def _to_integer(i: int):

    return Integer.from_int(i), lambda: python_string_integer(str(i))


@register_python_string
@rule
def _add_integer_str(l: str, r: str):

    return (
        python_string_integer(l) + python_string_integer(r),
        lambda: python_string_integer(f"({l} + {r})"),
    )


@expression
def python_string_bool(s: str) -> Boolean:
    ...


@expression
def bool_python_string(b: Boolean) -> str:
    ...


@register_python_string
@rule
def _other_things_string(b: str, l: str, r: str):
    yield bool_python_string(python_string_bool(b)), b
    yield python_string_bool(b).if_(
        python_string_integer(l), python_string_integer(r)
    ), lambda: python_string_integer(f"{l} if {b} else {r}")
    yield python_string_integer(l) < python_string_integer(
        r
    ), lambda: python_string_bool(f"({l} < {r})")
    yield python_string_integer(l) - python_string_integer(
        r
    ), lambda: python_string_integer(f"({l} - {r})")


@register_python_string
@rule
def _to_shape_zero():
    return Vec[Integer].create(), lambda: python_string_shape("tuple()")


@register_python_string
@rule
def _to_shape_one(i: str):
    return Vec.create(python_string_integer(i)), lambda: python_string_shape(f"({i},)")


@register_python_string
@rule
def _to_shape_two(i: str, j: str):
    return (
        Vec.create(python_string_integer(i), python_string_integer(j)),
        lambda: python_string_shape(f"({i}, {j})"),
    )


@register_python_string
@rule
def _to_shape_three(i: str, j: str, k: str):
    return (
        Vec.create(
            python_string_integer(i), python_string_integer(j), python_string_integer(k)
        ),
        lambda: python_string_shape(f"({i}, {j}, {k})"),
    )


@register_python_string
@rule
def _getitem_str(s: str, i: str):
    return (
        python_string_shape(s)[python_string_integer(i)],
        lambda: python_string_integer(f"{s}[{i}]"),
    )


@register_python_string
@rule
def _to_shape_four(i: str, j: str, k: str, l: str):
    return (
        Vec.create(
            python_string_integer(i),
            python_string_integer(j),
            python_string_integer(k),
            python_string_integer(l),
        ),
        lambda: python_string_shape(f"({i}, {j}, {k}, {l})"),
    )


@register_python_string
@rule
def _to_shape_take_drop(s: str, i: str):
    yield (
        python_string_shape(s).take(python_string_integer(i)),
        lambda: python_string_shape(f"{s}[:{i}]"),
    )
    yield (
        python_string_shape(s).drop(python_string_integer(i)),
        lambda: python_string_shape(f"{s}[{i}:]"),
    )


@register_python_string
@rule
def _int_multiple_str(l: str, r: str):
    yield (
        python_string_integer(l) * python_string_integer(r),
        lambda: python_string_integer(f"({l} * {r})"),
    )


def ones(shape: Shape):
    @Abstraction.from_fn
    def idx_fn(indices: Indices) -> Integer:
        return Integer.from_int(1)

    return Array.create(shape, idx_fn)


python_eval_rules = RulesRepeatFold()

rule_groups["python_eval"] = python_eval_rules
register_python_eval = python_eval_rules.append


import numpy
import itertools


@expression
def array_to_ndarray(a: Array[Integer]) -> numpy.ndarray:
    ...


@register_python_eval
@rule
def _eval_array_str(s: str):
    def result():
        locals_: typing.Dict = {}
        eval(
            compile(s, filename="<string>", mode="exec"),
            {"np": numpy, "itertools": itertools},
            locals_,
        )
        return locals_["array"]

    return (
        array_to_ndarray(python_string_array(s)),
        result,
    )


# ten = Integer.from_int(10)

# res = array_to_ndarray((Array.range(ten) + ones(Vec.create(ten))) @ Array.range(ten))
# execute(res)
