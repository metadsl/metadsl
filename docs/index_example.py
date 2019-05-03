import metadsl

class Number(metadsl.Instance):
    @metadsl.call(lambda self, other: Number)
    def __add__(self, other: "Number") -> "Number":
        ...

    @staticmethod
    @metadsl.call(lambda i: Number)
    def from_int(i: int) -> "Number":
        ...


@metadsl.RuleApplier
@metadsl.RulesRepeatFold
@metadsl.rule(None, Number)
def add_zero(x: int, y: Number):
    return Number.from_int(x) + y, lambda: y if x == 0 else None

assert add_zero(Number.from_int(0) + Number.from_int(10)) == Number.from_int(10)