# dep

from __future__  import annotations

from dataclasses import dataclass
from functools   import cached_property
from pathlib     import Path

import os

from .data   import Meta, Tags, TagUtil
from .config import LibraryConfig
from .util   import JSONFile, SomePath, resolve_parents


# folders

@dataclass(frozen=True)
class Folder:
    meta: Meta

    # load

    @classmethod
    def load(
            cls,
            library_root: Path,
            folder_name:  str,
            config: LibraryConfig | None = None
    ) -> Folder:
        config = config or LibraryConfig()
        path_root = library_root / Path(folder_name)
        path_meta = path_root.joinpath(config.folder_meta_json)
        try:
            meta_raw = JSONFile.read(path_meta)
            meta = Meta.from_dict(meta_raw)
        except FileNotFoundError:
            meta = Meta(
                name=folder_name,
                path_root=path_root
            )
            JSONFile.write(path_meta, meta.to_dict())
        return cls(meta)


# library

class Library:
    # const

    _UNCACHE_ON_UPDATE = [
        "tags", "folder_paths"
    ]

    # constr

    def __init__(
            self,
            library_root: SomePath,
            config: LibraryConfig | None = None
    ):
        self._path_root: Path = Path(library_root)
        self._config = config or LibraryConfig()
        self._paths  = self._config.resolve(self._path_root)

        self._folders: list[Folder] = []

        self._init_library()
        self.rescan()

    # external (filesystem)

    def _init_library(self) -> None:
        should_write_config = True
        try:
            config_raw = JSONFile.read(self._paths.config_json)
            config_read = LibraryConfig.from_dict(config_raw)
            if config_read == self._config:
                should_write_config = False # keep if meta is equal
            else:
                # overwrite / write new config if different
                to_remove = config_read.resolve(self._path_root)
                to_remove.config_json.unlink()                # delete old files
                to_remove.cached_json.unlink(missing_ok=True) # ..
        except FileNotFoundError:
            pass
        if should_write_config:
            JSONFile.write(
                self._paths.config_json,
                self._config.to_dict()
            )

    def rescan(self) -> None:
        scanned = [
            f for f in os.listdir(self._path_root)
            if f[0] != "." # exclude sys dirs
        ]
        for f in scanned:
            self._folders.append(
                Folder.load(self._path_root, f, self._config)
            )
        self._uncache_deps()

    # internal

    @property
    def folders(self) -> list[Folder]:
        return self._folders.copy()

    @cached_property
    def folder_paths(self) -> list[Path]:
        return [
            f.meta.path_root for f in self._folders
        ]

    @cached_property
    def tags(self) -> Tags:
        return TagUtil.combine(*[
            f.meta.tags for f in self._folders
        ])

    def add_folders(self, *folders: Folder):
        self._folders.extend(folders)
        self._uncache_deps()

    def _uncache_deps(self):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)