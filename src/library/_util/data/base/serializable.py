# dep

from __future__ import annotations

from abc    import ABC, abstractmethod
from typing import Any

from ...._util.file import JSONFile, SomePath


# types

type _SerializedShallow = str|list|dict
type Serialized = str|list[_SerializedShallow]|dict[str, _SerializedShallow]


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
    def _parse(cls, data: Any|Serialized, **kwargs: Any) -> T:
        pass

    # conversions

    @abstractmethod
    def serialize(self, **kwargs: Any) -> Serialized:
        pass

    @classmethod
    def from_serialized(cls, serialized: Serialized, **kwargs: Any) -> Serializable:
        return cls(serialized, **kwargs)

    # file

    def write(self, outfile: SomePath, **kwargs: Any) -> None:
        serialized = self.serialize(**kwargs)
        JSONFile.write(outfile, serialized)

    @classmethod
    def read(cls, infile: SomePath, **kwargs: Any) -> Serializable:
        serialized = JSONFile.read(infile)
        return cls.from_serialized(serialized, **kwargs)