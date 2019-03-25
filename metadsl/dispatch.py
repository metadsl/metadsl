# """
# Mechanisms for replacing expression with other expression using dispatching logic.
# """

# import dataclasses
# import typing
# from .expressions import *

# __all__ = ["dispatch"]


# @dataclasses.dataclass(frozen=True)
# class PossibleReplacement:
#     expression: Expression
#     replacement_function: typing.Callable


# PossibleReplacements = typing.Iterable[PossibleReplacement]

# DispatchFunction = typing.Callable[[Box], PossibleReplacements]

# def dispatch_repeatedly(dispatch_function: DispatchFunction, expr: Expression) -> Expression:

#     Expressions.fold()

# def dispatch_value(dispatch: DispatchFunction, box: Box) -> IntermediateType:
#     return box, dispatch(box)


# def dispatch_operation(
#     dispatch: DispatchFunction, box: Box[Operation[typing.Tuple[IntermediateType, ...]]]
# ) -> IntermediateType:
#     replacements = 
#     def map_arg


# """
# Takes a dispatcher and a box and 
# """
