from .conversion import *


class TestConvertIdentity:
    def test_matches_type(self):
        assert convert_identity_rule(convert(int, 1)) == 1

    def test_doesnt_match_type(self):
        assert convert_identity_rule(convert(int, "hi")) == convert(int, "hi")
