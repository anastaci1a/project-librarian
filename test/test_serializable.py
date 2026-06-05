# dep

from datetime import datetime
from os       import PathLike
from pathlib  import Path
from typing   import TypedDict, Any, Self, override

from library._util.data.base import * # only for testing


# Serializable subclasses

class DateTimeSerializable(Serializable[datetime]):
    @classmethod
    def _parse(cls, unparsed: Any | JSONValue, **kwargs: Any) -> datetime:
        if isinstance(unparsed, str):
            return datetime.fromisoformat(unparsed)
        if isinstance(unparsed, datetime):
            return unparsed
        print(type(unparsed))
        raise NotImplementedError

    def serialize(self, **kwargs: Any) -> JSONValue:
        return self._data.isoformat()

class PathSerializable(Serializable[Path]):
    @classmethod
    def _parse(cls, unparsed: Any | JSONValue, **kwargs: Any) -> Path:
        if isinstance(unparsed, str | PathLike):
            return Path(unparsed)
        if isinstance(unparsed, Path):
            return unparsed
        raise NotImplementedError

    def serialize(self, **kwargs: Any) -> JSONValue:
        return str(self._data)


# SerializableCollection subclass(es)

class MetaTypes(TypedDict):
    name: str
    date: DateTimeSerializable
    path: PathSerializable

class Meta(SerializableCollection[MetaTypes]):
    _ArgTypes = MetaTypes

    @override
    @classmethod
    def new(
            cls,
            name: str,
            date: str | datetime | DateTimeSerializable,
            path: str | Path | PathSerializable
    ) -> Self:
        return super().new(
            name=name,
            date=date,
            path=path
        )


# test

def test_serializable():
    data = {
        "name": "Test",
        "date": datetime.now(), # date
        "path": Path("./")      # path
    }
    meta = Meta(data)

    print(data)      # (unparsed)
    print(meta.data) # expected: dict[str, JSONValue | Serializable]


# main

if __name__ == "__main__":
    test_serializable()