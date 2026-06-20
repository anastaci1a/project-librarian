# dep

from datetime import datetime
from pathlib  import Path
from typing   import Self, TypedDict, override

from .base import SerializableCollection
from .data import SerializableDateTime, SerializablePath


# serializable collection

class MetaData(TypedDict):
    name:          str
    description:   str
    date_created:  SerializableDateTime # TODO: NotRequired[...] support
    date_modified: SerializableDateTime
    path_icon:     SerializablePath

class Meta(SerializableCollection[MetaData]):
    # const

    _DataTypes = MetaData

    # factory

    @override
    @classmethod
    def create(
            cls, *,
            name:          str = "Untitled",
            description:   str            | None = None,
            date_created:  str | datetime | None = None,
            date_modified: str | datetime | None = None,
            path_icon:     str | Path     | None = None
    ) -> Self:
        return super().create(
            name=name,
            description=description,
            date_created=date_created,
            date_modified=date_modified,
            path_icon=path_icon
        )