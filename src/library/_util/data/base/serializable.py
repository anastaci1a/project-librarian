# dep

from __future__ import annotations

from abc    import ABC, abstractmethod
from typing import Any, Self

from ...._util.file import JSONFile, SomePath


# typing utils

type JSONPrimitive = None | bool | int | float | str
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]

def is_jsonvalue(value: Any) -> bool:
    if isinstance(value, None | bool | int | float | str):
        return True

    if isinstance(value, list):
        return all(
            is_jsonvalue(item) for item in value
        )

    if isinstance(value, dict):
        return all(
            isinstance(k, str) and is_jsonvalue(v)
            for k, v in value.items()
        )

    return False

def is_serializable(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, Serializable)


# data

class Serializable[T](ABC):
    # constr

    def __init__(self, unparsed: Any, **kwargs: Any) -> None:
        self._data = type(self)._parse(unparsed, **kwargs)
        self._data: T = type(self)._parse(unparsed, **kwargs)

    # prop

    @property
    def data(self) -> T:
        return self._data # unsafe by default

    # parsing

    @classmethod
    @abstractmethod
    def _parse(cls, unparsed: Any|JSONValue, **kwargs: Any) -> T:
        raise NotImplementedError

    # conversions

    @abstractmethod
    def serialize(self, **kwargs: Any) -> JSONValue:
        raise NotImplementedError

    @classmethod
    def from_serialized(cls, serialized: JSONValue, **kwargs: Any) -> Self:
        return cls(serialized, **kwargs)

    # file

    def write(self, outfile: SomePath, **kwargs: Any) -> None:
        serialized = self.serialize(**kwargs)
        JSONFile.write(outfile, serialized)

    @classmethod
    def read(cls, infile: SomePath, **kwargs: Any) -> Self:
        serialized = JSONFile.read(infile)
        return cls.from_serialized(serialized, **kwargs)