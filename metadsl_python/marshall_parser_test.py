import pytest
import marshal
from .marshall_parser import marshall_parser


@pytest.mark.parametrize(
    "o",
    [True, False, None, StopIteration, ..., 0],
)
def test_parser(o: object) -> None:
    res = marshall_parser.parse(marshal.dumps(o))
    print(res.pretty())
