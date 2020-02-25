import collections.abc
import dataclasses
import typing

__all__ = ["safe_merge", "Item", "UnhashableMapping", "HashableMapping"]

T = typing.TypeVar("T")
V = typing.TypeVar("V")


@dataclasses.dataclass
class Item(typing.Generic[T, V]):
    key: T
    value: V


@dataclasses.dataclass(init=False, frozen=True)
class HashableMapping(collections.abc.Mapping, typing.Generic[T, V]):
    """
    Like a dictionary, but immutable and hashable.
    """

    _items: typing.Tuple[typing.Tuple[T, V], ...]

    def __init__(self, mapping: typing.Mapping[T, V]):
        object.__setattr__(
            self, "_items", tuple((k, v) for k, v in mapping.items())
        )

    def __hash__(self):
        return hash(self._items)

    def __getitem__(self, key: T) -> V:
        for item in self._items:
            if item[0] == key:
                return item[1]
        raise KeyError()

    def __iter__(self):
        for item in self._items:
            yield item[0]

    def __len__(self):
        return len(self._items)


@dataclasses.dataclass(init=False)
class UnhashableMapping(collections.abc.MutableMapping, typing.Generic[T, V]):
    """
    Like a dictionary, but can have unhashable keys.
    """

    _items: typing.List[Item[T, V]]

    def __init__(self, *items: Item[T, V]):
        self._items = list(items)

    def __getitem__(self, key: T) -> V:
        item = self._find_item(key)
        return item.value

    def __setitem__(self, key: T, value: V) -> None:
        try:
            item = self._find_item(key)
        except KeyError:
            item = Item(key, value)
            self._items.append(item)
        else:
            item.value = value

    def __delitem__(self, key: T) -> None:
        self._items.remove(self._find_item(key))

    def _find_item(self, key: T) -> Item[T, V]:
        for item in self._items:
            if item.key == key:
                return item
        raise KeyError()

    def __iter__(self):
        for item in self._items:
            yield item.key

    def __len__(self):
        return len(self._items)


def safe_merge(
    *mappings: typing.Mapping[T, V],
    dict_constructor: typing.Type[typing.MutableMapping] = dict,
) -> typing.Mapping[T, V]:
    """
    Combing mappings by merging the dictionaries. It raises a ValueError
    if there are duplicate keys and they are not equal.
    """
    res: typing.MutableMapping[T, V] = dict_constructor()
    for mapping in mappings:
        for key, value in mapping.items():
            if key in res:
                if res[key] != value:
                    raise ValueError()
            else:
                res[key] = value
    return res
