import dataclasses
import typing

from .expressions import *
from .calls import *
from .rules import *
from .matching import *

__all__ = ["Replacements", "Replacement", "ReplacementsSequence"]

T = typing.TypeVar("T")
Replacement = typing.Tuple[T, typing.Callable[[], typing.Optional[T]]]
T_Callable = typing.TypeVar("T_Callable", bound=typing.Callable[..., Replacement[T]])
PureReplacement = typing.Tuple[T, T]
T_PureCallable = typing.TypeVar("T_PureCallable", bound=typing.Callable[..., PureReplacement[T]])


@dataclasses.dataclass
class Replacements:
    rules: typing.Tuple[Rule, ...] = dataclasses.field(default=tuple())
    _rule: Rule = dataclasses.field(init=False)

    def register(
        self, *arg_types: ArgType
    ) -> typing.Callable[[T_Callable], T_Callable]:
        def inner(function: T_Callable, arg_types=arg_types, self=self) -> T_Callable:
            self.rules += (match_rule(arg_types, function),)
            self._update_rule()
            return function

        return inner

    def register_pure(
        self, *arg_types: ArgType
    ) -> typing.Callable[[T_PureCallable], T_PureCallable]:
        def inner(function: T_PureCallable, arg_types=arg_types, self=self) -> T_PureCallable:
            self.rules += (pure_match_rule(arg_types, function),)
            self._update_rule()
            return function

        return inner

    def __post_init__(self):
        self._update_rule()

    def _update_rule(self):
        execute_all = rule_sequence(*self.rules)
        execute_many_times = rule_repeat(execute_all)
        execute_fold = rule_fold(execute_many_times)
        execute_fold_many_times = rule_repeat(execute_fold)
        self._rule = execute_fold_many_times

    def __call__(self, val: ValueType[T]) -> T:
        """
        Applies all the functions rules until no more apply, recursively in the tree.
        """
        expr = to_expression(val)
        replaced_expr = self._rule(expr)  # type: ignore
        if replaced_expr is None:
            return val  # type: ignore
        return from_expression(replaced_expr)


@dataclasses.dataclass
class ReplacementsSequence:
    replacements: typing.List[Replacements]

    def __init__(self, *replacements: Replacements):
        self.replacements = list(replacements)

    def __call__(self, val: ValueType[T]) -> T:
        for replacement in self.replacements:
            val = replacement(val)
        return val  # type: ignore
