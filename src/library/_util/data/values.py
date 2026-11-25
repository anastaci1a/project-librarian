# dep

from datetime import datetime
from pathlib  import Path
from typing   import override

from ..file  import JSONValue, SomePath
from .serial import SerializableValue


# individual pieces of data

class SerializableDateTime(SerializableValue[datetime | str, datetime]):
    @override
    @classmethod
    def _parse(cls, unparsed: datetime | str, /) -> datetime:
        if isinstance(unparsed, str):
            return datetime.fromisoformat(unparsed)
        return super()._parse(unparsed)

    @override
    def serialize(self, /) -> JSONValue:
        return self._data.isoformat()

class SerializablePath(SerializableValue[SomePath, Path]):
    def __fspath__(self, /) -> str:
        return str(self._data)

    @override
    @classmethod
    def _parse(cls, unparsed: SomePath, /) -> Path:
        return Path(unparsed)

    @override
    def serialize(self, /) -> JSONValue:
        return self.__fspath__()
