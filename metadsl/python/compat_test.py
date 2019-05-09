import metadsl.python.pure as py_pure
import metadsl.python.compat as py_compat
from metadsl import *


class TestInteger:
    def test_from_int(self):
        assert convert(py_pure.Integer, 10) == py_pure.Integer.from_int(10)

    def test_add(self):
        one = py_pure.Integer.from_int(1)
        assert py_compat.Integer(one) + 10 == py_compat.Integer(
            one + py_pure.Integer.from_int(10)
        )


class TestTuple:
    def test_from_tuple(self):
        assert convert(
            py_pure.Tuple[py_pure.Integer], (0, 1)
        ) == py_pure.Tuple.from_items(
            py_pure.Integer, py_pure.Integer.from_int(0), py_pure.Integer.from_int(1)
        )

    def test_integer_tuple_getitem(self):
        i = py_pure.Tuple.from_items(
            py_pure.Integer, py_pure.Integer.from_int(0), py_pure.Integer.from_int(1)
        )
        assert py_compat.IntegerTuple(i)[0] == py_compat.Integer(
            i[py_pure.Integer.from_int(0)]
        )


class TestOptional:
    def test_none(self):
        assert convert(
            py_pure.Optional[py_pure.Boolean], None
        ) == py_pure.Optional.none(py_pure.Boolean)

    def test_some(self):
        assert convert(
            py_pure.Optional[py_pure.Boolean], True
        ) == py_pure.Optional.some(py_pure.Boolean.from_bool(True))


class TestUnion:
    def test_from_left(self):
        assert convert(
            py_pure.Union[py_pure.Integer, py_pure.Boolean], 1
        ) == py_pure.Union.left(
            py_pure.Integer, py_pure.Boolean, py_pure.Integer.from_int(1)
        )

    def test_from_right(self):
        assert convert(
            py_pure.Union[py_pure.Integer, py_pure.Boolean], True
        ) == py_pure.Union.right(
            py_pure.Integer, py_pure.Boolean, py_pure.Boolean.from_bool(True)
        )
