# dep

from __future__  import annotations

from collections.abc import Mapping
from configparser    import ParsingError
from dataclasses     import dataclass, field
from datetime        import datetime
from pathlib         import Path
from types           import MappingProxyType
from typing          import Any, cast

import inspect

from library.util import ArgParse


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

@dataclass
class Meta:
    # props

    name:          str              = "Untitled"
    description:   str              = ""
    tags:          Tags | TagsInput = field(default_factory=dict)
    date_created:  datetime         = field(default_factory=datetime.now)
    date_modified: datetime         = field(default_factory=datetime.now)
    path_root:     Path | None      = None
    path_icon:     Path | None      = None

    # freeze tags

    def __post_init__(self):
        self.tags = TagUtil.freeze(self.tags)

    # sys

    def __key(self) -> tuple:
        return (
            self.name, self.description,
            self.tags,
            self.date_created, self.date_modified,
            self.path_root,    self.path_icon
        )

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Meta) -> bool:
        if isinstance(other, Meta):
            return self.__key() == other.__key()
        return NotImplemented

    # method

    def to_dict(self) -> dict:
        data = self.__dict__.copy()
        for k in ("date_created", "date_modified", "path_root", "path_icon"):
            if data[k] is None:
                data.pop(k); continue
            data[k] = str(data.get(k))
        data["tags"] = TagUtil.serialize(data["tags"])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Meta:
        return cls._from_unparsed(**data)

    @classmethod
    def from_args(cls, **kwargs: Any):
        keys = dict(inspect.getmembers(cls))["__dataclass_fields__"].keys()
        args_filtered = {
            k: kwargs[k]
            for k in kwargs.keys() if k in keys
        }
        return cls._from_unparsed(**args_filtered)

    @classmethod
    def _from_unparsed(
            cls,
            name:          Any = None,
            description:   Any = None,
            tags:          Any = None,
            date_created:  Any = None,
            date_modified: Any = None,
            path_root:     Any = None,
            path_icon:     Any = None,

            **kwargs: Any # allow but ignore extraneous args
    ) -> Meta:
        def raise_invalid(meta: Any = "UNSET"):
            if meta != "UNSET":
                raise ParsingError(f"Invalid metadata: {meta}")
            else:
                raise ParsingError("Invalid metadata.")

        # type checking / initial parsing

        for test_type in (
            name, description,
            date_created, date_modified,
            path_root, path_icon
        ):
            if not isinstance(test_type, str|None):
                raise_invalid(test_type)

        if not isinstance(tags, dict|None):
            raise_invalid(str(tags))
        if tags is not None:
            for k in tags.keys():
                t = tags.get(k)
                if not isinstance(t, list|set):
                    raise_invalid(f"{t} ({k})")
            tags = {
                k: {str(s) for s in v}
                for k, v in tags.items()
            }

        # final parsing

        args = {
            "name":          ArgParse.str_or_none(name),
            "description":   ArgParse.str_or_none(description),
            "tags":          tags,
            "date_created":  ArgParse.datetime_or_none(date_created),
            "date_modified": ArgParse.datetime_or_none(date_modified),
            "path_root":     ArgParse.path_or_none(path_root),
            "path_icon":     ArgParse.path_or_none(path_icon)
        }

        return Meta(
            **{k: v for k, v in args.items() if v is not None}
        )