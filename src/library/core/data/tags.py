# dep

from collections.abc import Mapping
from types           import MappingProxyType
from typing          import Any, Self, TypeGuard, override

from ..._util.data.base import Serializable, JSONValue


# types

type TagsData       = Mapping[str, frozenset[str]]
type TagValuesInput = list[str] | tuple[str, ...] | set[str] | frozenset[str]
type TagsInput      = Mapping[str, TagValuesInput]

def is_tagsinput(value: Any) -> TypeGuard[TagsInput]:
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

class Tags(Serializable[TagsData]):
    @override
    @classmethod
    def _parse(
            cls,
            unparsed: TagsInput | Self | None = None,
            /,
            **kwargs: Any
    ) -> TagsData:
        if unparsed is None:
            return MappingProxyType({})

        if is_tagsinput(unparsed):
            frozen: dict[str, frozenset[str]] = {
                k: frozenset(v)
                for k, v in unparsed.items()
            }
            return MappingProxyType(frozen)

        return super()._parse(unparsed, **kwargs)

    @override
    def serialize(self, **kwargs: Any) -> JSONValue:
        unfrozen: dict[str, list[str]] = {
            k: sorted([s for s in v])
            for k, v in self.data.items()
        }

        return unfrozen

    # util

    @classmethod
    def combine(
            cls,
            *to_combine: TagsInput | Self,
            **kwargs
    ) -> Self:
        combined: dict[str, set[str]] = {}

        for item in to_combine:
            data = item.data if isinstance(item, cls) else item

            for k, v in data.items():
                combined.setdefault(k, set()).update(v)

        return cls(combined, **kwargs)