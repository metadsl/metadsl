from __future__ import annotations

import warnings
import pkgutil
from importlib.abc import Loader
from types import CodeType
from typing import Iterable
from hypothesis import example, given, settings, HealthCheck
import hypothesmith

from .code_data import CodeData


def test_modules():
    # Instead of params, iterate in test so that:
    # 1. the number of tests is consistant accross python versions pleasing xdist running multiple versions
    # 2. pushing loading of all modules inside generator, so that fast samples run first
    for code in module_codes():
        verify_code(code)


@given(source_code=hypothesmith.from_node())
@settings(suppress_health_check=(HealthCheck.filter_too_much, HealthCheck.too_slow))
@example("a")
@example("class A: pass\nclass A: pass\n")
def test_generated(source_code):
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
    resulting_code = CodeData.from_code(code).to_code()
    assert code_to_primitives(code) == code_to_primitives(resulting_code)
    assert code == resulting_code


code_attributes = tuple(
    name
    for name in dir(CodeType)
    if name.startswith("co_")
    # Don't compare generated co_lines iterator returned in Python 3.10
    # When co_lntob is removed in 3.12, we need to figured out how to adapt.
    # TODO: look at how co_lines works and make sure we can duplicate logic for mapping
    # https://docs.python.org/3/whatsnew/3.10.html?highlight=co_lines#pep-626-precise-line-numbers-for-debugging-and-other-tools
    and name != "co_lines"
)


def code_to_primitives(code: CodeType) -> dict[str, object]:
    """
    Converts a code object to primitives, for better pytest diffing
    """
    return {
        name: (
            # Recursively transform constants
            getattr(code, name)
            if name != "co_consts"
            else tuple(
                code_to_primitives(a) if isinstance(a, CodeType) else a
                for a in getattr(code, name)
            )
        )
        for name in code_attributes
    }


def code_to_dict(code: CodeType) -> dict[str, object]:
    """
    Converts a code object to a dict for testing
    """
    return {name: getattr(code, name) for name in dir(code)}
