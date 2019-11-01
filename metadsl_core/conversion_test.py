from metadsl import execute, ExpressionReference
from .conversion import *
from .maybe import *
from .rules import *


class TestConvertIdentity:
    def test_matches_type(self):
        assert execute(Converter[int].convert(1)) == Maybe.just(1)

    def test_doesnt_match_type(self):
        assert not list(
            convert_identity_rule(
                ExpressionReference.from_expression(Converter[str].convert(1))
            )
        )

    def test_matches_convert(self):
        assert execute(Converter[int].convert(Maybe.just(1))) == Maybe.just(1)
        assert (
            execute(Converter[int].convert(Maybe[int].nothing()))
            == Maybe[int].nothing()
        )


class TestConvertToMaybe:
    def test_just(self):
        assert execute(Converter[Maybe[int]].convert(1)) == Maybe.just(Maybe.just(1))

    def test_nothing(self):
        assert execute(Converter[Maybe[int]].convert(None)) == Maybe.just(
            Maybe[int].nothing()
        )
