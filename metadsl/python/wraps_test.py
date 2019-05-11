import metadsl.python.expressions as py
import metadsl.python.wraps as py_wraps
from metadsl import *


class TestInteger:
    def test_from_int(self):
        assert convert(py.Integer, 10) == py.Integer.from_int(10)

    def test_add(self):
        one = py.Integer.from_int(1)
        assert py_wraps.Integer(one) + 10 == py_wraps.Integer(
            one + py.Integer.from_int(10)
        )


class TestTuple:
    def test_from_tuple(self):
        assert convert(
            py.Tuple[py.Integer], (0, 1)
        ) == py.Tuple.from_items(
            py.Integer, py.Integer.from_int(0), py.Integer.from_int(1)
        )

    def test_integer_tuple_getitem(self):
        i = py.Tuple.from_items(
            py.Integer, py.Integer.from_int(0), py.Integer.from_int(1)
        )
        assert py_wraps.IntegerTuple(i)[0] == py_wraps.Integer(
            i[py.Integer.from_int(0)]
        )


class TestOptional:
    def test_none(self):
        assert convert(
            py.Optional[py.Boolean], None
        ) == py.Optional.none(py.Boolean)

    def test_some(self):
        assert convert(
            py.Optional[py.Boolean], True
        ) == py.Optional.some(py.Boolean.from_bool(True))


class TestUnion:
    def test_from_left(self):
        assert convert(
            py.Union[py.Integer, py.Boolean], 1
        ) == py.Union.left(
            py.Integer, py.Boolean, py.Integer.from_int(1)
        )

    def test_from_right(self):
        assert convert(
            py.Union[py.Integer, py.Boolean], True
        ) == py.Union.right(
            py.Integer, py.Boolean, py.Boolean.from_bool(True)
        )
