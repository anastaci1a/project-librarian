# dep

from collections.abc import Mapping
from types           import MappingProxyType
from typing import Any, Self, TypeGuard, Iterable

from ..._util.data.base import Serializable, JSONValue


# types

type TagsData  = Mapping[str, frozenset[str]]
type TagsInput = Mapping[str, Iterable[str]]

def is_tagsinput(value: Any) -> TypeGuard[TagsInput]:
    return (
        isinstance(value, Mapping)
        and all(
            isinstance(k, str)
            and isinstance(v, Iterable)
            and all(isinstance(tag, str) for tag in v)
            for k, v in value.items()
        )
    )



# tags

class Tags(Serializable[TagsData]):
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
                str(k): frozenset(v)
                for k, v in unparsed.items()
            }
            return MappingProxyType(frozen)

        return super()._parse(unparsed, **kwargs)

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
            *to_combine: Self,
            **kwargs
    ) -> Self:
        combined: dict[str, set[str]] = {}

        for tags in to_combine:
            for k, v in tags.data.items():
                combined.setdefault(k, set()).update(v)

        return cls(combined, **kwargs)