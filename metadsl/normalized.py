"""
Normalized expressions, for deduping and single replacements.

IDs should be consistant accross replacements.
"""
from __future__ import annotations
import dataclasses
import typing
import itertools

from .expressions import *


__all__ = ["ExpressionReference"]

ID = typing.NewType("ID", int)
Hash = typing.NewType("Hash", int)

HashID = typing.Tuple[Hash, ID]


@dataclasses.dataclass
class NormalizedExpression:
    function: typing.Callable
    args: typing.Tuple[Hash, ...]
    kwargs: typing.Dict[str, Hash]


@dataclasses.dataclass
class NormalizedExpressionLiteral:
    value: object


@dataclasses.dataclass
class NormalizedExpressions:
    # mapping of ID to either NormalizedExpression or literal values
    expressions: typing.Dict[
        ID, typing.Union[NormalizedExpression, NormalizedExpressionLiteral]
    ] = dataclasses.field(default_factory=dict)
    # mapping of hashses to ids
    hashes: typing.Dict[Hash, ID] = dataclasses.field(default_factory=dict)

    def get(self, hash_: Hash) -> object:
        ref = self.expressions[self.hashes[hash_]]
        if isinstance(ref, NormalizedExpressionLiteral):
            return ref.value
        return ref.function(
            *(self.get(a) for a in ref.args),
            **{k: self.get(v) for k, v in ref.kwargs.items()}
        )

    def bfs(self, hash_: Hash) -> typing.Iterable[Hash]:
        """
        breadth first search
        """
        seen: typing.Set[Hash] = set()
        to_see: typing.List[Hash] = [hash_]

        while to_see:
            hash_ = to_see.pop(0)
            yield hash_
            seen.add(hash_)
            ref = self.expressions[self.hashes[hash_]]
            if isinstance(ref, NormalizedExpressionLiteral):
                continue

            for child_hash in list(ref.args) + list(ref.kwargs.values()):
                if child_hash not in seen:
                    to_see.append(child_hash)

    def add(self, expr: object, prev_hash: typing.Optional[Hash]) -> Hash:
        """
        Add an expression, replacing the previous hash with it.
        """
        normalized_expr: typing.Union[NormalizedExpression, NormalizedExpressionLiteral]
        if isinstance(expr, Expression):
            prev_expr = self.expressions[self.hashes[prev_hash]] if prev_hash else None
            if (
                prev_expr
                and isinstance(prev_expr, NormalizedExpression)
                and prev_expr.function == expr.function
            ):
                prev_args = prev_expr.args
                prev_kwargs = prev_expr.kwargs
            else:
                prev_args = tuple()
                prev_kwargs = {}

            # get the new args and kwargs, passing in the IDs of the old ones if we have them
            arg_hashes = tuple(
                self.add(arg, prev_arg_hash)
                for arg, prev_arg_hash in itertools.zip_longest(
                    expr.args, prev_args, fillvalue=None
                )
            )
            kwarg_hashes = {
                k: self.add(v, prev_kwargs.get(k, None)) for k, v in expr.kwargs.items()
            }
            hash_ = Hash(
                hash((expr.function, arg_hashes, frozenset(kwarg_hashes.items())))
            )
            normalized_expr = NormalizedExpression(
                expr.function, arg_hashes, kwarg_hashes
            )
        else:
            try:
                hash_ = Hash(hash((type(expr), expr)))
            except TypeError:
                hash_ = Hash(hash((type(expr), id(expr))))
            normalized_expr = NormalizedExpressionLiteral(expr)

        self._add_normalized_expr(normalized_expr, hash_, prev_hash)
        return hash_

    def _add_normalized_expr(
        self,
        expr: typing.Union[NormalizedExpression, NormalizedExpressionLiteral],
        hash_: Hash,
        prev_hash: typing.Optional[Hash],
    ):
        if hash_ in self.hashes:
            # alias the old hash to the new id if we had it
            if prev_hash:
                self.hashes[prev_hash] = self.hashes[hash_]

        # otherwise add this as a new expression, using hash as ID if a previous one hasn't been supplied.
        id_ = self.hashes[prev_hash] if prev_hash else ID(hash_)
        self.expressions[id_] = expr
        self.hashes[hash_] = id_


T = typing.TypeVar("T")


@dataclasses.dataclass
class ExpressionReference(typing.Generic[T]):
    hash_: Hash
    expressions: NormalizedExpressions

    @classmethod
    def from_expression(cls, expr: T) -> ExpressionReference:
        expressions = NormalizedExpressions()
        return cls(expressions.add(expr, None), expressions)

    def replace(self, new_expr: T) -> None:
        self.expressions.add(new_expr, self.hash_)

    def to_expression(self) -> T:
        return self.expressions.get(self.hash_)  # type: ignore

    def child_references(self) -> typing.Iterable[ExpressionReference]:
        """
        returns a breadth first search of the graph starting a the root node
        """
        for child_hash in self.expressions.bfs(self.hash_):
            yield ExpressionReference(child_hash, self.expressions)
