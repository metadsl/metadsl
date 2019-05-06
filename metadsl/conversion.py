"""
Useful for to convert object to boxed types.
"""
import typing

__all__ = ["register_converter", "convert"]
T = typing.TypeVar("T")

convert_type = typing.Callable[[typing.Type[T], object], T]

converters: typing.List[convert_type] = []


def convert(type: typing.Type[T], value: object) -> T:
    """
    Converts a value to a certain type.
    """
    for converter in converters:
        res = converter(type, value)
        if res != NotImplemented:
            return res
    raise NotImplementedError(f"Cannot convert {value} to {type}")

def register_converter(converter: convert_type) -> None:
    """
    Registers a converter to use. The converter should take in a type and a value, 
    and return that value converted to the type if it can or NotImplemented.
    """
    converters.append(converter)
