"""
Normalized expressions, for deduping and single replacements.

IDs should be consistant accross replacements.
"""
from __future__ import annotations
import dataclasses
import typing
import itertools
import collections
import functools


from .expressions import *


__all__ = [
    "ExpressionReference",
    "NormalizedExpression",
    "NormalizedExpressions",
    "Parent",
    "Children",
    "hash_value",
    "Hash",
    "ID",
]

ID = typing.NewType("ID", int)
Hash = typing.NewType("Hash", int)


@dataclasses.dataclass(frozen=True)
class Parent:
    hash: Hash
    key: typing.Union[str, int]


@functools.singledispatch
def hash_value(value: object) -> int:
    """
    Computes some hash for a value that should be stable. Either use the built in hash, or if we cannot
    (like the object is mutable) then use the id.

    It's a single dispatch function so that you can register custom hashes for objects you don't control.
    """
    try:
        return Hash(hash((type(value), value)))
    except TypeError:
        return Hash(hash((type(value), id(value))))


@dataclasses.dataclass
class Children:
    args: typing.List[Hash]
    kwargs: typing.Dict[str, Hash]

    def references(self) -> typing.Iterable[typing.Tuple[typing.Union[str, int], Hash]]:
        return itertools.chain(enumerate(self.args), self.kwargs.items())


def compute_hash(value: object, children: typing.Optional[Children]) -> Hash:
    if children:
        assert isinstance(value, Expression)
        return Hash(
            hash(
                (
                    value.function,
                    tuple(children.args),
                    frozenset(children.kwargs.items()),
                )
            )
        )
    return Hash(hash_value(value))


@dataclasses.dataclass
class NormalizedExpression:
    children: typing.Optional[Children]
    value: object
    id: ID
    parents: typing.Set[Parent] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class NormalizedExpressions:
    # Expressions, topologically sorted, with the root expression at the end.

    expressions: collections.OrderedDict[
        Hash, NormalizedExpression
    ] = dataclasses.field(default_factory=collections.OrderedDict)

    # mapping of IDs to hashes for this set of expression
    ids: typing.Dict[ID, Hash] = dataclasses.field(default_factory=dict)

    next_id: ID = ID(0)
    # THe first hash  added. Used when adding a new expression, so we can record the left
    # most hash and delete  every hash before that
    _first_hash: typing.Optional[Hash] = None

    def add(
        self,
        expr: object,
        prev: typing.Optional[
            typing.Tuple[
                typing.Optional[Hash],
                collections.OrderedDict[Hash, NormalizedExpression],
            ]
        ] = None,
    ) -> Hash:
        """
        Does a depth addition of the expression to the graph, keeping all the nodes
        added in topological order, because the children will all be visisted after
        the parent.
        """

        children: typing.Optional[Children]

        prev_id: typing.Optional[ID]
        prev_args: typing.Optional[typing.List[Hash]]
        prev_kwargs: typing.Optional[typing.Dict[str, Hash]]
        prev_expressions: typing.Optional[
            collections.OrderedDict[Hash, NormalizedExpression]
        ]

        if prev:
            prev_hash, prev_expressions = prev
            if prev_hash:
                prev_ref = prev_expressions[prev_hash]
                prev_id = prev_ref.id
                if (
                    isinstance(prev_ref.value, Expression)
                    and isinstance(expr, Expression)
                    and prev_ref.value.function == expr.function
                ):
                    assert prev_ref.children
                    prev_args = prev_ref.children.args
                    prev_kwargs = prev_ref.children.kwargs
                else:
                    prev_args = None
                    prev_kwargs = None
            else:
                prev_id = None
                prev_args = None
                prev_kwargs = None
        else:
            prev_expressions = None
            prev_id = None
            prev_args = None
            prev_kwargs = None

        if isinstance(expr, Expression):
            children = Children([], {})
            for i, arg in enumerate(expr.args):
                arg_hash = self.add(
                    arg,
                    (
                        prev_args[i] if prev_args and i < len(prev_args) else None,
                        prev_expressions,
                    )
                    if prev_expressions
                    else None,
                )
                children.args.append(arg_hash)

                # Update expression with child, so that points to same one
                expr.args[i] = self.expressions[arg_hash].value
            for k, v in expr.kwargs.items():
                kwarg_hash = self.add(
                    v,
                    (
                        prev_kwargs.get(k, None) if prev_kwargs else None,
                        prev_expressions,
                    )
                    if prev_expressions
                    else None,
                )
                children.kwargs[k] = kwarg_hash

                # Update expression with child, so that points to same one
                expr.kwargs[k] = self.expressions[kwarg_hash].value
        else:
            children = None

        hash = compute_hash(expr, children)

        if children:
            for key, child_hash in children.references():
                self.expressions[child_hash].parents.add(Parent(hash, key))

        if not self._first_hash:
            self._first_hash = hash
        if hash not in self.expressions:
            id = self._get_new_id(prev_id)
            self.expressions[hash] = NormalizedExpression(children, expr, id)
            self.ids[id] = hash
        return hash

    def replace(self, hash: typing.Optional[Hash], expr: object) -> None:
        new_expressions = NormalizedExpressions(
            next_id=self.next_id
        )
        if not hash:
            # If we didn't get a hash, we are replacing the root node
            root_hash = next(iter(reversed(self.expressions)))
            root_expr = expr
        else:
            # Otherwise, we are replacing a child node
            # In which case, we update its parents, and get the root noode
            for parent in self.expressions[hash].parents:
                value = self.expressions[parent.hash].value
                assert isinstance(value, Expression)
                if isinstance(parent.key, str):
                    value.kwargs[parent.key] = expr
                else:
                    value.args[parent.key] = expr

            root_hash = self._get_root(hash)
            root_expr = self.expressions[root_hash].value
        new_expressions.add(root_expr, (root_hash, self.expressions))
        self.expressions = new_expressions.expressions
        self.ids = new_expressions.ids
        self.next_id = new_expressions.next_id

    def _get_new_id(self, prev_id: typing.Optional[ID]) -> ID:
        if prev_id and prev_id not in self.ids:
            return prev_id
        id = self.next_id
        self.next_id = ID(self.next_id + 1)
        assert id not in self.ids
        return id

    def _get_root(self, hash: Hash) -> Hash:
        parents = list(self.expressions[hash].parents)
        if parents:
            return self._get_root(parents[0].hash)
        return hash

    def _assert_expressions_topological_sorted(self) -> None:
        """
        All expressions should be after their children
        """
        for i, expr in enumerate(self.expressions.values()):
            if not expr.children:
                continue
            for _, child_hash in expr.children.references():
                # Children should be to the left of their parents
                assert self._index_of_hash(child_hash) < i

    def _index_of_hash(self, hash: Hash) -> int:

        for i, hash_ in enumerate(self.expressions.keys()):
            if hash_ == hash:
                return i
        raise RuntimeError()

    def _all_children(self, hash: Hash) -> typing.Set[Hash]:
        ref = self.expressions[hash]
        s = {hash}
        if not ref.children:
            return s
        for _, child_hash in ref.children.references():
            s.update(self._all_children(child_hash))
        return s

    def _assert_parents_children_consistant(self) -> None:
        """
        Asserts that parents match the children.

        For each expression, verifies that all children have this node as a parent, and all parents
        have this node as a child.
        """

        for hash, ref in self.expressions.items():
            for parent in ref.parents:
                key = parent.key
                parent_ref = self.expressions[parent.hash]
                assert parent_ref.children
                if isinstance(key, str):
                    assert parent_ref.children.kwargs[key] == hash
                else:
                    assert parent_ref.children.args[key] == hash

            if not ref.children:
                continue
            for key, child_hash in ref.children.references():
                child_ref = self.expressions[child_hash]
                assert Parent(key=key, hash=hash) in child_ref.parents

    def _assert_hashes_accurate(self):
        for hash, ref in self.expressions.items():
            assert hash == compute_hash(ref.value, ref.children)

    def _assert_children_match_values(self):
        for hash, ref in self.expressions.items():
            value = ref.value
            if not ref.children:
                assert not isinstance(value, Expression)
                continue
            assert isinstance(value, Expression)

            for i, arg in enumerate(ref.children.args):
                assert self.expressions[arg].value is value.args[i]

            for k, kwarg in ref.children.kwargs.items():
                assert self.expressions[kwarg].value is value.kwargs[k]

    def _assert_ids_match(self):
        for id, hash in self.ids.items():
            assert self.expressions[hash].id == id


T = typing.TypeVar("T")


@dataclasses.dataclass
class ExpressionReference(typing.Generic[T]):
    # Hash that we refer to. If it is None, then it is the last  expression by default
    expressions: NormalizedExpressions
    _hash: typing.Optional[Hash] = dataclasses.field(default=None, repr=False)

    def __post_init__(self):
        self.verify_integrity()

    @property
    def hash(self) -> Hash:
        return self._hash or self.root_hash

    @property
    def root_hash(self) -> Hash:
        return next(iter(reversed(self.expressions.expressions)))

    @classmethod
    def from_expression(cls, expr: T) -> ExpressionReference:
        expressions = NormalizedExpressions()
        expressions.add(expr)
        return cls(expressions)

    @property
    def normalized_expression(self) -> NormalizedExpression:
        return self.expressions.expressions[self.hash]

    def replace(self, new_expr: T) -> None:
        self.expressions.replace(self._hash, new_expr)
        self._hash = None

        # Optional, this could be disabled to improve performance
        self.verify_integrity()

    @property
    def children(self) -> typing.Iterable[ExpressionReference]:
        """
        Returns all the children of the graph, starting from the root node
        and ending in the leaf nodes.
        """
        root_node = True
        for k, v in reversed(self.expressions.expressions.items()):
            yield ExpressionReference(self.expressions, None if root_node else k)
            root_node = False

    def verify_integrity(self) -> None:
        """
        Verifies a number of properties about the data structures
        """

        expressions = self.expressions.expressions

        assert self.hash in expressions

        # Order
        self.expressions._assert_expressions_topological_sorted()

        all_children = self.expressions._all_children(self.root_hash)
        all_keys = set(expressions.keys())
        assert all_children == all_keys

        # IDs
        assert len(self.expressions.ids) == len(expressions)
        self.expressions._assert_ids_match()

        # Parents
        self.expressions._assert_parents_children_consistant()

        # Hashes
        self.expressions._assert_hashes_accurate()

        # Children
        self.expressions._assert_children_match_values()
