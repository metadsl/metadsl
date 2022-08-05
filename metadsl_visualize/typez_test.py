import json

import pytest
from metadsl.expressions import Expression
from metadsl_core import Integer, Vec

from metadsl_visualize.typez import expr_to_json_value, json_value_to_expr


@pytest.mark.parametrize(
    "v",
    [
        pytest.param(Integer.from_int(0), id='integer'),
        pytest.param(Vec.create(Integer.from_int(0)), id='vec'),
    ]
)
def test_to_from_json(v: Expression) -> None:
    json_value =  expr_to_json_value(v)
    assert json_value_to_expr(json_value) == v
