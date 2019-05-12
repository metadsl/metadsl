# from __future__ import annotations

# import typing

# from .wraps import *
# from .expressions import *


# T_some = typing.TypeVar("T_some", bound="SomeExpr")


# class SomeExpr(Expression):
#     @classmethod
#     @expression
#     def create(cls: typing.Type[T_some]) -> T_some:
#         ...


# @expression
# def create_expr() -> Expression:
#     ...


# @expression
# def fn(a: SomeExpr, b: Expression) -> SomeExpr:
#     ...


# class SomeWrap(SomeExpr):
#     pass


# @wrap(fn)
# def fn_wrapped(a: object, b: object) -> SomeWrap:
#     ...


# def test_wrap_function():
#     result = fn_wrapped(SomeWrap.create(), create_expr())
#     assert result == SomeWrap(fn, (SomeExpr.create(), create_expr()))


# T = typing.TypeVar("T")

# T_expr = typing.TypeVar("T_expr", bound="Expr")


# class Expr(Expression, typing.Generic[T]):
#     @classmethod
#     @expression
#     def create(cls: typing.Type[T_expr]) -> T_expr:
#         ...


# class WrapExpr(Expr[int]):
#     ...


# def test_wrap_returns_generic():
#     assert WrapExpr.create() == WrapExpr(Expr.create, ())


# T_number = typing.TypeVar("T_number", bound="Number")


# class Number(Expression):
#     @expression
#     def __add__(self, other: Number) -> Number:
#         ...

#     @classmethod
#     @expression
#     def create(cls: typing.Type[T_number]) -> T_number:
#         ...


# class WrapNumber(Number):
#     @wrap_method
#     def __add__(self, other: object) -> WrapNumber:
#         ...


# def test_wrap_method():
#     n = WrapNumber.create()
#     k = Number.create()
#     assert n + k == WrapNumber(Number.__add__, (Number.create(), Number.create()))


# class List(Expression, typing.Generic[T]):
#     @expression
#     def __getitem__(self, idx: Number) -> T:
#         ...


# @expression
# def create_list_number() -> List[Number]:
#     ...


# class WrapListInt(Wrap[List[Number]]):
#     @wrap(List.__getitem__)
#     def __getitem__(self, idx: object) -> WrapNumber:
#         ...


# def test_wrap_method_generic():
#     l = create_list_number()
#     i = create_number()
#     assert WrapListInt(l)[i] == WrapNumber(l[i])
