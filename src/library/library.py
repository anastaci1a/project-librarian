# dep

from __future__  import annotations

import os

from dataclasses import dataclass
from functools   import cached_property
from pathlib     import Path

from .data   import Meta, Tags, TagUtil
from .config import LibraryConfig
from .util   import JSONFile, SomePath, resolve_parents


# folders

@dataclass
class Folder:
    meta: Meta

    # load

    @classmethod
    def load(
            cls,
            library_root: Path,
            folder_name:  str,
            schema:       LibraryConfig = LibraryConfig()
    ) -> Folder:
        path_root = library_root.joinpath(folder_name)
        path_meta = path_root.joinpath(schema.folder_meta_json)
        try:
            meta_raw = JSONFile.read(path_meta)
            meta     = Meta.from_dict(meta_raw)
        except FileNotFoundError:
            meta = Meta(
                name=folder_name,
                path_root=path_root
            )
            JSONFile.write(path_meta, meta.to_dict())
        return cls(meta)


# library

class Library:
    _UNCACHE_ON_UPDATE = [
        "tags", "folder_paths"
    ]

    # constr

    def __init__(
            self,
            library_root: SomePath,
            config:       LibraryConfig = LibraryConfig()
    ):
        self._path_root: Path = Path(library_root)
        self._folders: list[Folder] = []
        self._config: LibraryConfig = config
        self._paths:  LibraryConfig = LibraryConfig(
            config_json=self._path_root.joinpath(self._config.config_json),
            cached_json=self._path_root.joinpath(self._config.config_json),
        )

        self._init_library()
        self.rescan()

    # external (filesystem)

    def _init_library(self):
        JSONFile.write(
            self._paths.config_json,
            self._config.to_dict()
        )

    def rescan(self):
        scanned = [
            f for f in os.listdir(self._path_root)
            if f[0] != "." # exclude sys dirs
        ]
        for f in scanned:
            self._folders.append(
                Folder.load(self._path_root, f, self._config)
            )

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