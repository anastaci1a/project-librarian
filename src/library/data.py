# dep

from __future__  import annotations

from configparser import ParsingError
from dataclasses  import dataclass
from datetime     import datetime
from os           import PathLike
from pathlib      import Path
from types        import MappingProxyType
from typing       import Any

from .util import JSONFile


# export

type Tags = dict[str, set[str]]

def tags_combine(*tagsets: Tags):
    combined = {}
    for tags in tagsets:
        for k,v in tags.items():
            combined.setdefault(k, set())
            combined[k].update(v)
    return combined

@dataclass
class Meta:
    # prop

    name:          str      = "Untitled Project"
    description:   str      = ""
    tags:          Tags     = MappingProxyType({})
    date_created:  datetime = datetime.fromordinal(1)
    date_modified: datetime = datetime.fromordinal(1)
    path:          Path     = Path()
    icon:          Path     = Path()

    # sys

    def __key(self) -> tuple:
        return self.date_created, self.name

    def __hash__(self) -> int:
        print(self.__key())
        return hash(self.__key())

    def __eq__(self, other: Meta) -> bool:
        if isinstance(other, Meta):
            return self.__key() == other.__key()
        return NotImplemented

    # method

    def to_json(self, outfile: str | PathLike[str] = "") -> str:
        return JSONFile.write_dumps(
            outfile,
            self._to_json_serializable()
        )

    @classmethod
    def from_json(cls, infile: str | PathLike[str] = "") -> Meta:
        parsed = JSONFile.loads(infile)
        if isinstance(parsed, dict):
            return cls._from_unparsed(**parsed)
        return Meta()

    def _to_json_serializable(self):
        data = self.__dict__.copy()
        for k in ("date_created", "date_modified", "path", "icon"):
            data[k] = str(data.get(k))
        print(*data)

        return data

    @classmethod
    def _from_unparsed(
            cls,
            name:          Any = None,
            description:   Any = None,
            tags:          Any = None,
            date_created:  Any = None,
            date_modified: Any = None,
            path:          Any = None,
            icon:          Any = None
    ) -> Meta:
        for expected_str in (
            name, description,
            path, icon,
            date_created,
            date_modified
        ):
            if not isinstance(expected_str, str):
                raise ParsingError("Invalid metadata.")

        if not isinstance(tags, dict):
            raise ParsingError
        for k in tags.keys():
            t = tags.get(k)
            if not isinstance(t, list):
                raise ParsingError("Invalid metadata.")

        tags = MappingProxyType({
            k: {str(s) for s in v}
            for k,v in tags.items()
        })

        name, description = str(name),  str(description)
        path, icon        = Path(path), Path(icon)
        date_created      = datetime.fromisoformat(date_created)
        date_modified     = datetime.fromisoformat(date_modified)

        return Meta(
            name, description, tags,
            date_created, date_modified,
            path, icon
        )