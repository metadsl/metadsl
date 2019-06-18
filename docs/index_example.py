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
def add_zero(x: int, y: Number):
    return Number.from_int(x) + y, lambda: y if x == 0 else None


assert add_zero(Number.from_int(0) + Number.from_int(10)) == Number.from_int(10)
