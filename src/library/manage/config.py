# dep

from __future__ import annotations

from dataclasses import dataclass
from pathlib     import Path
from typing      import Self, TypedDict, override, Any

from ..                import Tags
from .._util           import SomePath
from .._util.data.base import SerializableCollection


# data

class _LibrarianConfigData(TypedDict):
    fileext_to_tag: dict[str, Tags]

def _get_config_args_default() -> dict:
    pass


# library config

class LibrarianConfig(SerializableCollection[_LibrarianConfigData]):
    @override
    @property
    def data(self) -> _LibrarianConfigData:
        return self._data

    @override
    @classmethod
    def create(
            cls,
            **data_unparsed_args: Any
    ) -> Self:
        kwargs = {}

        return super().create(
            **kwargs,
            args_defaults=_get_config_args_default()
        )


# paths

@dataclass(frozen=True)
class LibraryPaths:
    root:   Path
    config: LibrarianConfig

    @property
    def config_json(self) -> Path:
        return self.root / self.config.config_json

    @property
    def cached_json(self) -> Path:
        return self.root / self.config.cached_json

    def folder_meta_json(self, folder_root: SomePath) -> Path:
        return Path(folder_root) / self.config.folder_meta_json