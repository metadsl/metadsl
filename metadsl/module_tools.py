
import importlib
import typing
import sys
__all__ = ["export_from"]


def export_from(module_name: str, *submodules: str, local: typing.List[str]=[]) -> None:
    """
    Sets the  `__all__` for the module to be the union of all the __all__'s of the submodules,
    plus the locals.

    Needed so that the modules themselves are not present in the __init__.py file, but all the exports are.
    """
    m = sys.modules[module_name]
    m.__all__ = list(local) #type: ignore
    for submodule in submodules:
        m.__all__.extend(importlib.import_module("." + submodule, module_name).__all__)#type: ignore