# dep

from __future__  import annotations

from datetime import datetime
from pathlib  import Path
from typing   import Any, NotRequired, Self, TypedDict, override

from .tags import TagsInput, Tags

from ..._util           import File, SerializableDateTime, SerializablePath
from ..._util.data.base import SerializableCollection


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
    # const

    _DataTypes = MetaData

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
        provided = {
            "name":          name,
            "description":   description,
            "tags":          tags,
            "date_created":  date_created,
            "date_modified": date_modified if date_modified is not None else date_created,
            "path_icon":     path_icon
        }

        kwargs = _get_meta_args_default() | {
            k: v
            for k, v in provided.items()
            if v is not None
        }

        return super().create(**kwargs)

    # meta-specific

    def get_refreshed(self, root: Path) -> Meta:
        date_folder_created    = File.get_creation_date(root)
        date_folder_modified   = File.get_date_modified(root)
        date_children_modified = File.get_child_latest_date_modified(root, exclude_dotfiles=True)

        new_date_created = self.data["date_created"] or date_folder_created
        new_date_modified = (
                date_children_modified
                or date_folder_modified
                or self.data["date_modified"]
                or self.data["date_created"]
        )

        return Meta.create(
            **(self.data | {
                "date_created":  new_date_created,
                "date_modified": new_date_modified
            })
        )