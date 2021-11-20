from __future__ import annotations

import marshal

import pytest

from .marshal_data import MarshalledData


@pytest.mark.parametrize(
    "o",
    (
        pytest.param(None, id="None"),
        pytest.param(10, id="int"),
        pytest.param(b"abc", id="bytes"),
        pytest.param("abc", id="str"),
        pytest.param(("a",), id="tuple",),
        pytest.param(compile("a", "<str>", "exec"), id="code",),
    ),
)
def test_marshal_data(o):
    b = marshal.dumps(o)
    assert MarshalledData.from_bytes(b).to_bytes() == b
