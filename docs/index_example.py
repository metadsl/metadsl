from __future__ import annotations
import metadsl_all as m


class Number(m.Expression):
    @m.expression
    def __add__(self, other: Number) -> Number:
        ...

    @m.expression
    @classmethod
    def from_int(cls, i: int) -> Number:
        ...


@m.register_core
@m.rule
def add_zero(y: Number):
    yield Number.from_int(0) + y, y
    yield y + Number.from_int(0), y


assert m.execute(Number.from_int(0) + Number.from_int(10)) == Number.from_int(10)
