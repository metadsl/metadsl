import typing

__all__ = ["safe_merge"]

T = typing.TypeVar("T")
V = typing.TypeVar("V")


def safe_merge(*mappings: typing.Dict[T, V]) -> typing.Dict[T, V]:
    """
    Combing mappings by merging the dictionaries. It raises a ValueError
    if there are duplicate keys and they are not equal.
    """
    res: typing.Dict[T, V] = {}
    for mapping in mappings:
        for key, value in mapping.items():
            if key in res:
                if res[key] != value:
                    raise ValueError(
                        f"Got two different values {res[key]} and {value} for key {key} while merging"
                    )
            else:
                res[key] = value
    return res
