# dep

from __future__  import annotations

from collections.abc import Mapping
from configparser    import ParsingError
from dataclasses     import dataclass, field, replace
from datetime        import datetime
from pathlib         import Path
from types           import MappingProxyType
from typing          import Any, cast

from .util import ArgParse, FileData


# tags

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
            k: sorted([str(s) for s in v])
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


# meta

@dataclass(frozen=True)
class Meta:
    # props

    name:          str              = "Untitled"
    description:   str              = ""
    tags:          Tags | TagsInput = field(default_factory=dict)
    date_created:  datetime | None  = None
    date_modified: datetime | None  = None
    relpath_meta:  Path     | None  = None
    path_icon:     Path     | None  = None

    # init (freeze attrs)

    def __post_init__(self):
        object.__setattr__(
            self,
            "tags",
            TagUtil.freeze(self.tags)
        )

    # sys

    def __key(self) -> tuple:
        return (
            self.name, self.description,
            self.tags,
            self.date_created, self.date_modified,
            self.relpath_meta, self.path_icon
        )

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Meta) -> bool:
        if isinstance(other, Meta):
            return self.__key() == other.__key()
        return NotImplemented

    # copy with modif

    def get_refreshed(self, root: Path) -> Meta:
        date_folder_created    = FileData.get_creation_date(root)
        date_folder_modified   = FileData.get_date_modified(root)
        date_children_modified = FileData.get_child_latest_date_modified(root, exclude_dotfiles=True)

        new_date_created = self.date_created or date_folder_created
        new_date_modified = (
                date_children_modified
                or date_folder_modified
                or self.date_modified
                or self.date_created
        )

        return replace(
            self,
            date_created  = new_date_created,
            date_modified = new_date_modified
        )

    # method

    def to_dict(self) -> dict:
        data = self.__dict__.copy()
        for k in ("date_created", "date_modified", "relpath_meta", "path_icon"):
            if data[k] is None:
                data.pop(k); continue
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
            relpath_meta:  Any = None,
            path_icon:     Any = None,

            **kwargs: Any # allow but ignore extraneous args
    ) -> Meta:
        def raise_invalid(meta: Any = "UNSET"):
            if meta != "UNSET":
                raise ParsingError(f"Invalid metadata: {meta}")
            else:
                raise ParsingError("Invalid metadata.")

        # str/date type checking

        for test_str in (
            name, description,
            relpath_meta, path_icon
        ):
            if not isinstance(test_str, str|None):
                raise_invalid(test_str)

        for test_date in (
            date_created, date_modified
        ):
            if not isinstance(test_date, str|datetime|None):
                raise_invalid(test_date)

        # tags type checking / initial parsing

        if not isinstance(tags, dict|None):
            raise_invalid(str(tags))
        if tags is not None:
            for k in tags.keys():
                test_tag = tags.get(k)
                if not isinstance(test_tag, list|set):
                    raise_invalid(f"{test_tag} ({k})")
            tags = {
                k: {str(s) for s in v}
                for k, v in tags.items()
            }

        # final parsing

        args_parsed = {
            "name":          ArgParse.str_or_none(name),
            "description":   ArgParse.str_or_none(description),
            "tags":          tags,
            "date_created":  ArgParse.datetime_or_none(date_created),
            "date_modified": ArgParse.datetime_or_none(date_modified),
            "relpath_meta":  ArgParse.path_or_none(relpath_meta),
            "path_icon":     ArgParse.path_or_none(path_icon)
        }

        return cls(**{
            k: v for k, v in args_parsed.items() if v is not None
        })