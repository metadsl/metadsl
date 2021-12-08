from __future__ import annotations

import marshal
import warnings
import pkgutil
from importlib.abc import Loader
from types import CodeType
from typing import Iterable
from hypothesis import example, given
import pytest
import hypothesmith

from .code_data import CodeData


def test_code_data_from_modules():
    # Instead of params, iterate in test so that:
    # 1. the number of tests is consistant accross python versions pleasing xdist running multiple versions
    # 2. pushing loading of all modules inside generator, so that fast samples run first
    for code in module_codes():
        verify_code(code)


@given(source_code=hypothesmith.from_node())
@example("a")
@example("class A: pass\nclass A: pass\n")
def test_code_data_generated(source_code):
    code = compile(source_code, "<string>", "exec")
    verify_code(code)


def module_codes() -> Iterable[CodeType]:

    # In order to test the code_data, we try to get a sample of bytecode,
    # by walking all our packages and trying to load every module.
    # Note that although this doesn't require the code to be executable,
    # `walk_packages` does require it, so this will ignore any modules
    # which raise errors on import.

    with warnings.catch_warnings():
        # Ignore warning on find_module which will be deprecated in Python 3.12
        # Worry about it later!
        warnings.simplefilter("ignore")
        for mi in pkgutil.walk_packages(onerror=lambda _name: None):
            loader: Loader = mi.module_finder.find_module(mi.name)  # type: ignore
            try:
                code = loader.get_code(mi.name)  # type: ignore
            except SyntaxError:
                continue
            if code:
                yield code


def verify_code(code: CodeType) -> None:
    # Note: Make sure not to store a copy of the CodeData instance,
    # or if you do, delete if before trying to dump it.
    # marshalling will treat values with refernces differently sometimes
    # and store them as "refs" to prevent cycles, so the bytes will not be ==
    resulting_code = CodeData.from_code(code).to_code()
    gc.collect()

    # We start by comparing the data first and then the marshalled bytes.
    # Compares the bytes gives us the highest assurance that our parsing
    # was isomorphic, but also is harder to parse if there is an error.
    assert code_to_dict(resulting_code) == code_to_dict(code)

    assert marshal.dumps(resulting_code) == marshal.dumps(code)


def code_to_dict(code: CodeType) -> dict[str, object]:
    """
    Converts a code object to a dict for testing
    """
    return {
        name: getattr(code, name)
        for name in dir(code)
        if name.startswith("co_")
        # Don't compare generated co_lines iterator returned in Python 3.10
        # When co_lntob is removed in 3.12, we need to figured out how to adapt.
        # TODO: look at how co_lines works and make sure we can duplicate logic for mapping
        # https://docs.python.org/3/whatsnew/3.10.html?highlight=co_lines#pep-626-precise-line-numbers-for-debugging-and-other-tools
        and name != "co_lines"
    }
