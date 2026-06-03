# dep

from __future__  import annotations

from dataclasses import dataclass
from pathlib     import Path

import inspect

from .._util import SomePath


# config

@dataclass(frozen=True)
class LibraryConfig:
    # attrs

    config_json:      Path = Path(".library/config.json")
    cached_json:      Path = Path(".library/cached.json")
    folder_meta_json: Path = Path(".folder/meta.json")

    # sys

    def __key(self) -> tuple:
        return (
            self.config_json, self.cached_json,
            self.folder_meta_json
        )

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: LibraryConfig) -> bool:
        if isinstance(other, LibraryConfig):
            return self.__key() == other.__key()
        return NotImplemented

    # method

    def to_dict(self) -> dict[str, str]:
        r = self.__dict__.copy()
        for k in r.keys():
            r[k] = str(r[k])
        return r

    @classmethod
    def from_dict(cls, config: dict[str, str]) -> LibraryConfig:
        keys = dict(inspect.getmembers(cls))["__dataclass_fields__"].keys()
        return cls(**{
            k: Path(v) for k, v in config.items() if k in keys and v is not None
        })

    def resolve(self, library_root: SomePath) -> LibraryPaths:
        return LibraryPaths(Path(library_root), self)


# paths

@dataclass(frozen=True)
class LibraryPaths:
    root: Path
    config: LibraryConfig

    @property
    def config_json(self) -> Path:
        return self.root / self.config.config_json

    @property
    def cached_json(self) -> Path:
        return self.root / self.config.cached_json

    def folder_meta_json(self, folder_root: SomePath) -> Path:
        return Path(folder_root) / self.config.folder_meta_json