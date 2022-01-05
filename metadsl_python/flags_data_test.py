from __future__ import annotations

import inspect

import pytest

from .flags_data import to_flags_data, from_flags_data

import __future__  # isort:skip


@pytest.mark.parametrize(
    "flags",
    (
        pytest.param(0, id="no flags"),
        pytest.param(inspect.CO_OPTIMIZED, id="single"),
        pytest.param(inspect.CO_NOFREE, id="nofree single"),
        pytest.param(inspect.CO_NEWLOCALS & inspect.CO_OPTIMIZED, id="two combined"),
        pytest.param(
            inspect.CO_NEWLOCALS & inspect.CO_OPTIMIZED & inspect.CO_ASYNC_GENERATOR,
            id="three combined",
        ),
        pytest.param(
            __future__.CO_FUTURE_ABSOLUTE_IMPORT,  # type: ignore
            id="absolute import",
        ),
        pytest.param(
            __future__.CO_FUTURE_BARRY_AS_BDFL & inspect.CO_NEWLOCALS,  # type: ignore
            id="future and other flag",
        ),
    ),
)
def test_code_flags_data(flags: int):
    assert from_flags_data(to_flags_data(flags)) == flags
