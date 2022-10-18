import pytest

from metadsl.expressions import Expression, expression
from metadsl.typing_tools import get_type
from metadsl_core import Integer, Vec
from metadsl_visualize.typez import expr_to_json_value, json_value_to_expr


@expression
def placeholder_expr() -> int:
    ...


@pytest.mark.parametrize(
    "v",
    [
        pytest.param(Integer.from_int(0), id="integer"),
        pytest.param(
            Vec.create(Integer.from_int(0)), id="vec", marks=pytest.mark.xfail
        ),
        pytest.param(
            placeholder_expr(), id="placeholder_expr", marks=pytest.mark.xfail
        ),
    ],
)
def test_to_from_json(v: Expression) -> None:
    json_value = expr_to_json_value(v)
    new_v = json_value_to_expr(json_value)
    assert new_v == v
    assert get_type(new_v) == get_type(v)
