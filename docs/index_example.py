from __future__ import annotations
import metadsl


class Number(metadsl.Expression):
    @metadsl.expression
    def __add__(self, other: Number) -> Number:
        ...

    @metadsl.expression
    @classmethod
    def from_int(cls, i: int) -> Number:
        ...


@metadsl.rule
def add_zero(y: Number):
    yield Number.from_int(0) + y, y
    yield y + Number.from_int(0), y


assert metadsl.execute(
    Number.from_int(0) + Number.from_int(10), add_zero
) == Number.from_int(10)
