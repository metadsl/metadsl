"""
Rewrite rules for metadsl expressions
"""

from metadsl import export_from


from .normalize import *  # type: ignore
from .rules import *  # type: ignore
from .strategies import *  # type: ignore
from .combinators import *  # type: ignore


strategy = StrategyNormalize()
execute = Executor(strategy)
register = Registrator(strategy)

export_from(
    __name__,
    "normalize",
    "rules",
    "strategies",
    "combinators",
    local=["execute", "register"],
)

__version__ = "0.1.0"
