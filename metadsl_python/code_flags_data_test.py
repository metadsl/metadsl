from __future__ import annotations

import inspect

import pytest

from .code_flags_data import CodeFlagsData

import __future__  # isort:skip


@pytest.mark.parametrize(
    "flags",
    (
        pytest.param(0, id="no flags"),
        pytest.param(inspect.CO_OPTIMIZED, id="single"),
        pytest.param(inspect.CO_NOFREE, id="nofree single"),
        pytest.param(
            inspect.CO_NEWLOCALS & inspect.CO_OPTIMIZED, id="two combined"
        ),
        pytest.param(
            inspect.CO_NEWLOCALS
            & inspect.CO_OPTIMIZED
            & inspect.CO_ASYNC_GENERATOR,
            id="three combined",
        ),
        pytest.param(
            __future__.CO_FUTURE_ABSOLUTE_IMPORT,  # type: ignore
            id="absolute import",
        ),
        pytest.param(
            __future__.CO_FUTURE_BARRY_AS_BDFL  # type: ignore
            & inspect.CO_NEWLOCALS,
            id="future and other flag",
        ),
    ),
)
def test_code_flags_data(flags):
    assert CodeFlagsData.from_flags(flags).to_flags() == flags
