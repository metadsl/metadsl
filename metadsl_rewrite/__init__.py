"""
Rewrite rules for metadsl expressions
"""

from metadsl import export_from

from .combinators import *  # type: ignore
from .enum_rule import *  # type: ignore
from .normalize import *  # type: ignore
from .rules import *  # type: ignore
from .strategies import *  # type: ignore

strategy = StrategyNormalize()
execute: Executor = Executor(strategy)
register = Registrator(strategy)

export_from(
    __name__,
    "normalize",
    "rules",
    "strategies",
    "combinators",
    "enum_rule",
    local=["execute", "register"],
)

__version__ = "0.1.0"
