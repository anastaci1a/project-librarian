# dep

from __future__ import annotations

from abc    import ABC, abstractmethod
from typing import Any, Self

from ...._util.file import JSONFile, SomePath


# types

type JSONPrimitive = None | bool | int | float | str
type JSONValue = JSONPrimitive | list[JSONPrimitive] | dict[str, JSONPrimitive]


# data

class Serializable[T](ABC):
    # constr

    def __init__(self, value: Any, **kwargs: Any) -> None:
        self._value: T = self._parse(value, **kwargs)

    # prop

    @property
    def value(self) -> T:
        return self._value # unsafe by default

    # parsing

    @classmethod
    @abstractmethod
    def _parse(cls, data: Any|JSONValue, **kwargs: Any) -> T:
        pass

    # conversions

    @abstractmethod
    def serialize(self, **kwargs: Any) -> JSONValue:
        pass

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