# dep

from datetime import datetime
from os       import PathLike
from pathlib  import Path
from typing   import Any, override

from .base import JSONValue, Serializable


# individual pieces of data

class SerializableDateTime(Serializable[datetime]):
    # method

    @override
    @classmethod
    def _parse(cls, unparsed: Any | JSONValue, **kwargs: Any) -> datetime:
        if isinstance(unparsed, str):
            return datetime.fromisoformat(unparsed)
        raise NotImplementedError

    @override
    def serialize(self, **kwargs: Any) -> JSONValue:
        return self._data.isoformat()

class SerializablePath(Serializable[Path]):
    # method

    @override
    @classmethod
    def _parse(cls, unparsed: Any | JSONValue, **kwargs: Any) -> Path:
        if isinstance(unparsed, str | PathLike):
            return Path(unparsed)
        raise NotImplementedError

    @override
    def serialize(self, **kwargs: Any) -> JSONValue:
        return str(self._data)
