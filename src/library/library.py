# dep

from __future__  import annotations

from dataclasses import dataclass
from functools   import cached_property
from pathlib     import Path

import os

from .data   import Meta, Tags, TagUtil
from .config import LibraryConfig
from .util   import JSONFile, SomePath


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
        path_root = library_root / folder_name
        path_meta = path_root / config.folder_meta_json
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
            config: LibraryConfig|None = None,

            config_create_if_missing: bool = True,
            config_allow_overwrite:   bool = False
    ):
        self._folders: list[Folder] = []
        self._assign_config_and_paths(
            config,
            Path(library_root)
        )

        config_was_provided = config is not None
        self._init_library(
            config_was_provided,
            config_create_if_missing,
            config_allow_overwrite,
        )
        self.rescan()

    # util

    def _assign_config_and_paths(
            self,
            config: LibraryConfig | None,
            library_root: Path
    ):
        self._config = config or LibraryConfig()
        self._paths = self._config.resolve(library_root)

    # file init/loading

    def _init_library(self, config_was_provided: bool, create_if_missing: bool, allow_overwrite: bool) -> None:
        try:
            config_found_dict = JSONFile.read(self._paths.config_json)
            config_found = LibraryConfig.from_dict(config_found_dict)
            if not config_was_provided or config_found == self._config:
                # use existing config
                write_new_config = False
                self._assign_config_and_paths(config_found, self._paths.root)
            elif allow_overwrite:
                # delete old config and overwrite
                write_new_config = True
                to_remove = config_found.resolve(self._paths.root)
                to_remove.config_json.unlink() # delete old files
                to_remove.cached_json.unlink(missing_ok=True) # ..
            else:
                raise FileExistsError("Found existing configuration file(s), but config_allow_overwrite is disabled.")
        except FileNotFoundError:
            write_new_config = True # new config if none found
            if not create_if_missing:
                raise FileNotFoundError("Did not find configuration file(s), but create_if_missing is disabled.")
        # (write)
        if write_new_config:
            JSONFile.write(
                self._paths.config_json,
                self._config.to_dict()
            )

    def rescan(self) -> None:
        self._folders.clear()
        scanned = [
            d for d in os.scandir(self._paths.root)
            if d.is_dir() and not d.name.startswith(".") # only non-sys dirs
        ]
        for d in scanned:
            self._folders.append(
                Folder.load(self._paths.root, d.name, self._config)
            )
        self._uncache_props()

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
        self._uncache_props()

    def _uncache_props(self):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)