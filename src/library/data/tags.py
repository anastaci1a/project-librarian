# dep

from collections.abc import Mapping
from types           import MappingProxyType
from typing          import Any, Self, TypeGuard, cast, override

from .._util.data.serializable import SerializableValue
from .._util.file import JSONValue


# types

type TagsData       = Mapping[str, frozenset[str]]
type TagsInput      = Mapping[str, TagValuesInput]
type TagValuesInput = list[str] | tuple[str, ...] | set[str] | frozenset[str]

def is_tagsinput(value: Any, /) -> TypeGuard[TagsInput]:
    return (
        isinstance(value, Mapping)
        and all(
            isinstance(k, str)
            and isinstance(v, (list, tuple, set, frozenset))
            and all(isinstance(tag, str) for tag in v)
            for k, v in value.items()
        )
    )


# tags

class Tags(SerializableValue[TagsInput | None, TagsData]):
    @override
    @classmethod
    def _parse(cls, unparsed: TagsInput | None = None, /) -> TagsData:
        if unparsed is None:
            return MappingProxyType({})

        if not is_tagsinput(unparsed):
            raise TypeError("Expected tag names mapped to collections of strings")
        return MappingProxyType({k: frozenset(v) for k, v in unparsed.items()})

    @override
    def serialize(self, /) -> JSONValue:
        return cast(JSONValue, {k: sorted(v) for k, v in self.data.items()})

    # util

    @classmethod
    def combine(cls, /, *to_combine: TagsInput | Self) -> Self:
        combined: dict[str, set[str]] = {}

        for item in to_combine:
            data = item.data if isinstance(item, Tags) else item

            for k, v in data.items():
                combined.setdefault(k, set()).update(v)

        return cls(combined)
