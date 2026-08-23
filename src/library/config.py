# dep

from __future__ import annotations

from dataclasses import dataclass
from pathlib     import Path
from typing      import Self, TypedDict, override

from ._util           import SomePath
from ._util.data      import SerializablePath
from ._util.data.base import SerializableCollection


# data

class _LibraryConfigData(TypedDict):
    config_json:      SerializablePath
    cached_json:      SerializablePath
    folder_meta_json: SerializablePath

def _get_config_args_default():
    return {
        "config_json":      ".library/config.json",
        "cached_json":      ".library/cached.json",
        "folder_meta_json": ".folder/meta.json"
    }


# library config

class LibraryConfig(SerializableCollection[_LibraryConfigData]):
    # const

    _DataTypes = _LibraryConfigData

    # data

    @override
    @property
    def data(self) -> _LibraryConfigData:
        return None

    # factory

    @override
    @classmethod
    def create(
            cls,
            *,
            config_json:      SomePath | None = None,
            cached_json:      SomePath | None = None,
            folder_meta_json: SomePath | None = None
    ) -> Self:
        kwargs = {
            "config_json":      config_json,
            "cached_json":      cached_json,
            "folder_meta_json": folder_meta_json
        }

        return super().create(
            **kwargs,
            args_defaults=_get_config_args_default()
        )

    # ez props

    @property
    def config_json(self) -> Path:
        return self._data["config_json"].data

    @property
    def cached_json(self) -> Path:
        return self._data["cached_json"].data

    @property
    def folder_meta_json(self) -> Path:
        return self._data["folder_meta_json"].data

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

    # paths

    def resolve(self, library_root: SomePath) -> LibraryPaths:
        return LibraryPaths(Path(library_root), self)


# paths

@dataclass(frozen=True)
class LibraryPaths:
    root:   Path
    config: LibraryConfig

    @property
    def config_json(self) -> Path:
        return self.root / self.config.config_json

    @property
    def cached_json(self) -> Path:
        return self.root / self.config.cached_json

    def folder_meta_json(self, folder_root: SomePath) -> Path:
        return Path(folder_root) / self.config.folder_meta_json