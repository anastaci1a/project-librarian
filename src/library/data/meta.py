# dep

from __future__  import annotations

from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from pathlib  import Path
from typing   import Callable, Self, override

from .tags import TagsInput, Tags

from .._util           import FileSystem, Generator, SerializableDateTime, SerializablePath
from .._util.data.serializable import SerializableModel
from .._util.file import JSONValue


# meta

@dataclass(frozen=True, kw_only=True)
class Meta(SerializableModel):
    uid: str
    name: str
    tags: Tags
    date_created: SerializableDateTime
    date_modified: SerializableDateTime
    description: str | None = field(default=None, metadata={"omit_none": True})
    path_icon: SerializablePath | None = field(default=None, metadata={"omit_none": True})

    @classmethod
    def create(
            cls,
            *,
            uid:           str            | None = None,
            name:          str            | None = None,
            description:   str            | None = None,
            tags:          TagsInput      | None = None,
            date_created:  str | datetime | None = None,
            date_modified: str | datetime | None = None,
            path_icon:     str | Path     | None = None,
            uid_generator: Callable[[], str] = Generator.uid_generate
    ) -> Self:
        created = SerializableDateTime(date_created if date_created is not None else datetime.now())
        return cls(
            uid=uid_generator() if uid is None else uid,
            name="Untitled" if name is None else name,
            tags=Tags(tags),
            date_created=created,
            date_modified=created if date_modified is None else SerializableDateTime(date_modified),
            description=description,
            path_icon=None if path_icon is None else SerializablePath(path_icon),
        )

    # conversions

    @override
    @classmethod
    def deserialize(
            cls,
            serialized: JSONValue, /,
            *,
            discard_unknown_fields: bool = True,
            repair_with_defaults:   bool = False,
            uid_generator: Callable[[], str] = Generator.uid_generate
    ) -> Self:
        if not repair_with_defaults:
            return super().deserialize(
                serialized,
                discard_unknown_fields=discard_unknown_fields
            )
        if isinstance(serialized, dict):
            # Repair null fields as missing; retain unknown keys for strict validation.
            names = {f.name for f in fields(cls)}
            serialized = {k: v for k, v in serialized.items() if v is not None or k not in names}
        fields_to_repair = cls._decode_fields(serialized, discard_unknown_fields=discard_unknown_fields)
        return cls.create(**fields_to_repair, uid_generator=uid_generator)

    # meta-specific

    def get_reset(self) -> Self:
        return self.create(uid=self.uid, name=self.name)

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

        earliest = FileSystem.get_earliest_date_modified(children) or date_modified
        previous = self.date_created.data
        if previous.tzinfo is not None:
            date_modified = date_modified.astimezone(previous.tzinfo)
            earliest = earliest.astimezone(previous.tzinfo)
        date_created = min(date_modified, earliest, previous)

        return replace(self, date_created=SerializableDateTime(date_created),
                       date_modified=SerializableDateTime(date_modified))
