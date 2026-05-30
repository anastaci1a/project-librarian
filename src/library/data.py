# dep

from __future__  import annotations

from collections.abc import Mapping
from configparser    import ParsingError
from dataclasses     import dataclass, field
from datetime        import datetime
from pathlib         import Path
from types           import MappingProxyType
from typing          import Any, cast


# export

type Tags      = Mapping[str, frozenset[str]]
type TagsInput = Mapping[str, set[str]]

class TagUtil:
    @staticmethod
    def freeze(tags: TagsInput | None = None) -> Tags:
        frozen: dict[str, frozenset[str]] = {
            str(k): frozenset(str(tag) for tag in v)
            for k, v in (tags or {}).items()
        }
        return cast(Tags, MappingProxyType(frozen))

    @staticmethod
    def serialize(tags: Tags) -> dict[str, list[str]]:
        unfrozen: dict[str, list[str]] = {
            k: [str(s) for s in v]
            for k, v in tags.items()
        }
        return unfrozen

    @staticmethod
    def combine(*tagsets: TagsInput):
        combined: dict[str, set[str]] = {}
        for tags in tagsets:
            for k, v in tags.items():
                combined.setdefault(k, set())
                combined[k].update(v)
        return TagUtil.freeze(combined)

@dataclass
class Meta:
    # props

    name:          str              = "Untitled"
    description:   str              = ""
    tags:          Tags | TagsInput = field(default_factory=Mapping)
    date_created:  datetime         = field(default_factory=datetime.now)
    date_modified: datetime         = field(default_factory=datetime.now)
    path:          Path | None      = None
    icon:          Path | None      = None

    # freeze tags

    def __post_init__(self):
        self.tags = TagUtil.freeze(self.tags)

    # sys

    def __key(self) -> tuple:
        return self.date_created, self.name

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Meta) -> bool:
        if isinstance(other, Meta):
            return self.__key() == other.__key()
        return NotImplemented

    # method

    def to_dict(self) -> dict:
        data = self.__dict__.copy()
        for k in ("path", "icon", "date_created", "date_modified"):
            data[k] = str(data.get(k))
        data["tags"] = TagUtil.serialize(data["tags"])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Meta:
        return cls._from_unparsed(**data)

    @classmethod
    def _from_unparsed(
            cls,
            name:          Any = None,
            description:   Any = None,
            tags:          Any = None,
            date_created:  Any = None,
            date_modified: Any = None,
            path:          Any = None,
            icon:          Any = None,

            **kwargs: Any # allow but ignore extraneous args
    ) -> Meta:
        def raise_invalid():
            raise ParsingError("Invalid metadata.")

        # type checking

        for expected_str in (
            name, description,
            date_created, date_modified,
            path, icon
        ):
            if not isinstance(expected_str, str):
                raise_invalid()

        if not isinstance(tags, dict):
            raise_invalid()
        for k in tags.keys():
            t = tags.get(k)
            if not isinstance(t, list | set):
                raise_invalid()

        # parsing

        tags = {
            k: {str(s) for s in v}
            for k, v in tags.items()
        }

        name, description = str(name), str(description)
        date_created      = datetime.fromisoformat(date_created)
        date_modified     = datetime.fromisoformat(date_modified)
        path, icon        = Path(path), Path(icon)

        return Meta(
            name          = name,
            description   = description,
            tags          = tags,
            date_created  = date_created,
            date_modified = date_modified,
            path          = path,
            icon          = icon
        )