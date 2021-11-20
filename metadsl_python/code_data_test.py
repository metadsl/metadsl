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


# Special cases to test manually
SAMPLE_CODE = {"string": "a"}

code_params = [
    pytest.param(compile(str, "<str>", "exec"), id=name)
    for name, str in SAMPLE_CODE.items()
]

# In order to test the code_data, we try to get a sample of bytecode,
# by walking all our packages and trying to load every module.
# Note that although this doesn't require the code to be executable,
# `walk_packages` does require it, so this will ignore any modules
# which raise errors on import.
module_infos = pkgutil.walk_packages(onerror=lambda _name: None)
code_params += [
    pytest.param(code, id=mi.name)
    for mi in module_infos
    if (
        code := safe_get_code(
            cast(Loader, mi.module_finder.find_module(mi.name)), mi.name
        )
    )
]


@pytest.mark.parametrize("code", code_params)
def test_code_data(code: CodeType):
    # Note: Make sure not to store a copy of the CodeData instance,
    # or if you do, delete if before trying to dump it.
    # marshalling will treat values with refernces differently sometimes
    # and store them as "refs" to prevent cycles, so the bytes will not be ==
    resulting_code = CodeData.from_code(code).to_code()

    # We start by comparing the data first and then the marshalled bytes.
    # Compares the bytes gives us the highest assurance that our parsing
    # was isomorphic, but also is harder to parse if there is an error.
    assert code_to_dict(resulting_code) == code_to_dict(code)
    assert marshal.dumps(resulting_code) == marshal.dumps(code)


def code_to_dict(code: CodeType) -> dict[str, object]:
    """
    Converts a code object to a dict for testing
    """
    return {name: getattr(code, name) for name in dir(code) if name.startswith("co_")}
