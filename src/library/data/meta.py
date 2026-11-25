# dep

from attrs   import Factory, evolve, field, frozen
from pathlib import Path
from typing  import Callable, ClassVar, Self, override

from .._util             import FileSystem, Generator
from .._util.data        import SerializableDateTime, SerializablePath
from .._util.data.serial import SerializableModel
from .._util.file        import JSONValue, SomePath

from .tags import Tags


# meta util

def _optional_path(value: SomePath | SerializablePath | None, /) -> SerializablePath | None:
    return None if value is None else SerializablePath(value)


# meta

@frozen(kw_only=True)
class Meta(SerializableModel):
    omit_none: ClassVar[bool] = True

    # props

    uid:  str  = field(factory=Generator.uid_generate)
    name: str  = "Untitled"
    tags: Tags = field(default=None, converter=Tags)

    date_created: SerializableDateTime = field(
        factory=SerializableDateTime.now,
        converter=SerializableDateTime
    )
    date_modified: SerializableDateTime = field(
        default=Factory(lambda self: self.date_created, takes_self=True),
        converter=SerializableDateTime,
    )

    description: str              | None = None
    path_icon:   SerializablePath | None = field(default=None, converter=_optional_path)

    # serial

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
        values = cls._decode_fields(
            serialized,
            discard_unknown_fields=discard_unknown_fields,
            skip_none=repair_with_defaults
        )
        if repair_with_defaults:
            if "uid" not in values:
                values["uid"] = uid_generator()
        else:
            missing = {"uid", "name", "tags", "date_created", "date_modified"} - values.keys()
            if missing:
                raise TypeError(f"Missing required metadata fields: {sorted(missing)}")
        return cls(**values)

    # meta-specific

    def get_reset(self) -> Self:
        return type(self)(uid=self.uid, name=self.name)

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

        # noinspection PyTypeChecker
        return evolve(self, date_created=date_created, date_modified=date_modified)
