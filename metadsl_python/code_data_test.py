from __future__ import annotations

import marshal
import pkgutil
from importlib.abc import Loader
from types import CodeType
from typing import Optional, cast

import pytest

from .code_data import CodeData


def safe_get_code(loader: Loader, name: str) -> Optional[CodeType]:
    """
    Try to get the code for a module, but if syntax is wrong, just return None
    """
    try:
        return loader.get_code(name)
    except SyntaxError:
        return None


# In order to test the code_data, we try to get a sample of bytecode,
# by walking all our packages and trying to load every module.
# Note that although this doesn't require the code to be executable,
# `walk_packages` does require it, so this will ignore any modules
# which raise errors on import.
module_infos = pkgutil.walk_packages(onerror=lambda _name: None)
name_and_code = (
    (mi.name, code)
    for mi in module_infos
    if (
        code := safe_get_code(
            cast(Loader, mi.module_finder.find_module(mi.name)), mi.name
        )
    )
)


@pytest.mark.parametrize(
    "code", (pytest.param(code, id=name) for name, code in name_and_code)
)
def test_code_data(code: CodeType):
    code_data = CodeData.from_code(code)
    resulting_code = code_data.to_code()

    # We start by comparing the data first, then moving on to the code object,
    # and then the marshalled bytes.
    # In the end, the marshalled bytes give us the highest assurance that
    # our code parsing is isomoprhic, but it's the hardest to parse
    # when we do have errors
    assert code_to_dict(resulting_code) == code_to_dict(code)
    assert resulting_code == code
    # TODO: Debug why the marhsl is failing, by changing some back to original code
    # Then compare marshalled code objects to make sure they are the same
    assert marshal.dumps(resulting_code) == marshal.dumps(code)


def code_to_dict(code: CodeType) -> dict[str, object]:
    """
    Converts a code object to a dict for testing
    """
    return {name: getattr(code, name) for name in dir(code) if name.startswith("co_")}
