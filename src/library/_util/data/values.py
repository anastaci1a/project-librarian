# dep

from datetime import datetime
from os       import PathLike
from pathlib  import Path
from typing   import override

from ..file        import JSONValue
from .serializable import SerializableValue


# individual pieces of data

class SerializableDateTime(SerializableValue[str | datetime, datetime]):
    @override
    @classmethod
    def _parse(cls, unparsed: str | datetime, /) -> datetime:
        if isinstance(unparsed, str):
            return datetime.fromisoformat(unparsed)
        return super()._parse(unparsed)

    @override
    def serialize(self, /) -> JSONValue:
        return self._data.isoformat()

class SerializablePath(SerializableValue[str | PathLike, Path]):
    def __fspath__(self, /) -> str:
        return str(self._data)

    @override
    @classmethod
    def _parse(cls, unparsed: str | PathLike, /) -> Path:
        return Path(unparsed)

    @override
    def serialize(self, /) -> JSONValue:
        return self.__fspath__()
