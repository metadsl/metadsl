import pytest
from metadsl import NoMatch
from .conversion import *
from .maybe import *


class TestConvertIdentity:
    def test_matches_type(self):
        assert convert_identity_rule(Converter[int].convert(1)) == Maybe.just(1)

    def test_doesnt_match_type(self):
        with pytest.raises(NoMatch):
            convert_identity_rule(Converter[str].convert(1))


class TestConvertToMaybe:
    def test_just(self):
        assert convert_to_maybe(Converter[Maybe[int]].convert(1)) == Maybe.just(
            Converter[int].convert(1)
        )

    def test_nothing(self):
        assert convert_to_maybe(Converter[Maybe[int]].convert(None)) == Maybe.just(
            Maybe[int].nothing()
        )
