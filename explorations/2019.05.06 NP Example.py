import metadsl
import metadsl.python.pure as py_pure
import metadsl.numpy.pure as np_pure


a = np_pure.arange(
    py_pure.Optional.none(py_pure.Number),
    py_pure.Number.from_number(10),
    py_pure.Optional.none(py_pure.Number),
    py_pure.Optional.none(np_pure.DType),
)

a[
    py_pure.Union.left(
        py_pure.Integer, py_pure.Tuple[py_pure.Integer], py_pure.Integer.from_int(10)
    )
]

a[
    py_pure.Union.right(
        py_pure.Integer,
        py_pure.Tuple[py_pure.Integer],
        py_pure.Tuple.from_items(
            py_pure.Integer, py_pure.Integer.from_int(10), py_pure.Integer.from_int(10)
        ),
    )
]


@metadsl.pure_rule
def getitem_condense(a: np_pure.NDArray, left_idx: py_pure.Integer, right_idx: py_pure.Integer):
    return (
        a[
            py_pure.Union.left(
                py_pure.Integer, py_pure.Tuple[py_pure.Integer], left_idx
            )
        ][
            py_pure.Union.left(
                py_pure.Integer, py_pure.Tuple[py_pure.Integer], right_idx
            )
        ],
        a[
            py_pure.Union.right(
                py_pure.Integer,
                py_pure.Tuple[py_pure.Integer],
                py_pure.Tuple.from_items(py_pure.Integer, left_idx, right_idx),
            )
        ],
    )
