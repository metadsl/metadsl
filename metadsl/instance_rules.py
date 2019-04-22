import dataclasses
import typing

from .expressions import Expression, Instance
from .matching import MatchFunctionType, match_rule
from .rules import rule_fold, rule_repeat, rule_sequence

__all__ = ["replace_all"]

@dataclasses.dataclass
class ReplaceAll:
    match_functions: typing.List[MatchFunctionType]

    def __call__(self, instance: Instance) -> Instance:
        """
        Applies all the functions rules until no more apply, recursively in the tree.
        """
        execute_all = rule_sequence(*(match_rule(fn) for fn in self.match_functions))
        execute_many_times = rule_repeat(execute_all)
        execute_fold = rule_fold(execute_many_times)
        execute_fold_many_times = rule_repeat(execute_fold)

        expr = Expression.from_instance(instance)
        replaced_expr = execute_fold_many_times(expr)
        if replaced_expr is None:
            return instance
        return replaced_expr.instance

def replace_all(*fns: MatchFunctionType) -> ReplaceAll:
    return ReplaceAll(list(fns))
