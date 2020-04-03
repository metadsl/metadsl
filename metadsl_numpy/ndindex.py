# """
# Multidimensional indices

# from https://gist.github.com/asmeurer/4913d32da667690e49f4675822219cb3
# """
# from __future__ import annotations

# from metadsl import *
# import typing
# import numpy





# __all__ = ["NDIndex", "NumPyIndex"]

# NumPyIndexInnerType = typing.Union[slice, ellipsis, int]
# NumPyIndexType = typing.Union[NumPyIndexInnerType, typing.Tuple[NumPyIndexInnerType, ...]]


# PossibleWrappedType = 'typing.Union[NumPyIndexInnerType, NDIndexCompat]'

# class NDIndexCompat(Expression):
#     """
#     Multi dimensional index that when used on some array returns some subset
#     of the values
#     """

#     @expression
#     @classmethod
#     def wrap(cls, v: NumPyIndexType) -> NDIndex:
#         ...


#     @expression
#     def __getitem__(self, v: PossibleWrappedType) -> NDIndexCompat:
#         """

#         """
#         ...


#     @expression
#     def __add__(self, v: PossibleWrappedType) -> NDIndexCompat:
#         ...

#     @expression
#     def len(self)

#     @expression
#     def length