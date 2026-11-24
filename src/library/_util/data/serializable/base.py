# dep

from abc    import ABC, abstractmethod
from typing import Self

from ...file import JSONFile, JSONValue, SomePath


# base

class Serializable(ABC):
    # interf

    @abstractmethod
    def serialize(self, /) -> JSONValue:
        """Serialize to `JSONValue`"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized: JSONValue, /) -> Self:
        """Parse and initialize from `JSONValue`"""
        raise NotImplementedError

    # file util

    def write(self, outfile: SomePath, /) -> None:
        JSONFile.write(outfile, self.serialize())

    @classmethod
    def read(cls, infile: SomePath, /) -> Self:
        return cls.deserialize(JSONFile.read(infile))
