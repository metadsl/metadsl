"""
Useful for to convert object to boxed types.
"""
# import typing
# from .expressions import Expression

# __all__ = ["register_converter", "convert"]
# T_expression = typing.TypeVar("T_expression", bound=Expression)

# convert_type = typing.Callable[[typing.Type[T_expression], object], T_expression]

# converters: typing.List[convert_type] = []


# def convert(type: typing.Type[T_expression], value: object) -> T_expression:
#     """
#     Converts a value to a certain expression type.
#     """
#     for converter in converters:
#         res = converter(type, value)
#         if res != NotImplemented:
#             return res
#     raise NotImplementedError(f"Cannot convert {value} to {type}")

# def register_converter(converter: convert_type) -> None:
#     """
#     Registers a converter to use. The converter should take in a type and a value, 
#     and return that value converted to the type if it can or NotImplemented.
#     """
#     converters.append(converter)
