# dep

from __future__  import annotations

from datetime import datetime
from pathlib  import Path
from typing   import Any, NotRequired, Self, TypedDict, override

from .tags import TagsInput, Tags

from .._util           import FileSystem, SerializableDateTime, SerializablePath
from .._util.data.base import SerializableCollection


# data

class MetaData(TypedDict):
    name:          str
    tags:          Tags
    date_created:  SerializableDateTime
    date_modified: SerializableDateTime

    description:   NotRequired[str]
    path_icon:     NotRequired[SerializablePath]

def _get_meta_args_default() -> dict[str, Any]:
    now = datetime.now()

    return {
        "name": "Untitled",
        "tags": {},
        "date_created": now,
        "date_modified": now,
    }


# meta

class Meta(SerializableCollection[MetaData]):
    # data
    
    @override
    @property
    def data(self) -> MetaData:
        return self._data.copy()
    
    # factory

    @override
    @classmethod
    def create(
            cls,
            *,
            name:          str            | None = None,
            description:   str            | None = None,
            tags:          TagsInput      | None = None,
            date_created:  str | datetime | None = None,
            date_modified: str | datetime | None = None,
            path_icon:     str | Path     | None = None
    ) -> Self:
        kwargs = {
            "name":          name,
            "description":   description,
            "tags":          tags,
            "date_created":  date_created,
            "date_modified": date_modified if date_modified is not None else date_created,
            "path_icon":     path_icon
        }

        return super().create(
            **kwargs,
            args_defaults=_get_meta_args_default()
        )

    # meta-specific

    def get_reset(self) -> Self:
        return self.create(
            name=self.data["name"]
        )

    def get_refreshed(self, root: Path) -> Self:
        children = FileSystem.get_children(
            root,
            sublevels=5,
            include_root=False,
            exclude_dotfiles=True,
            exclude_folders=True
        )

        date_modified = (
            FileSystem.get_latest_date_modified(children)
            or FileSystem.get_date_modified(root)
        )

        date_created = min(
            date_modified,
            FileSystem.get_earliest_date_modified(children) or date_modified,
            self.data["date_created"].data,
        )

        return type(self).create(
            **(self.data | {
                "date_created":  date_created,
                "date_modified": date_modified
            })
        )