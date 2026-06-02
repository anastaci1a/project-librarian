# dep

from __future__  import annotations

from dataclasses import dataclass
from functools   import cached_property
from pathlib     import Path

import os

from .data   import Meta, Tags, TagUtil
from .config import LibraryConfig
from .util   import JSONFile, SomePath, File


# folders

@dataclass(frozen=True)
class Folder:
    meta: Meta

    # sys

    def __eq__(self, other: Folder) -> bool:
        if isinstance(other, Folder):
            return self.meta.name == other.meta.name
        return NotImplemented

    # load

    @classmethod
    def load(
            cls,
            library_root: Path,
            folder_name:  str,
            config:       LibraryConfig | None = None,
            update_meta:  bool                 = False
    ) -> Folder:
        config = config or LibraryConfig()
        folder_root = library_root / folder_name
        path_meta   = folder_root / config.folder_meta_json

        try:
            meta_raw = JSONFile.read(path_meta)
            meta = Meta.from_dict(meta_raw)
        except FileNotFoundError:
            return cls.create(
                library_root, Meta(name=folder_name),
                config=config, update_meta=update_meta
            )
        if update_meta:
            meta = cls._update_meta(folder_root, meta)
        JSONFile.write(path_meta, meta.to_dict())
        return cls(meta)

    @classmethod
    def create(
            cls,
            library_root: Path,
            meta:         Meta,
            config:       LibraryConfig | None = None,
            update_meta:  bool = False
    ) -> Folder:
        config = config or LibraryConfig()
        folder_root = library_root / meta.name
        path_meta   = folder_root / config.folder_meta_json

        folder_root.mkdir(exist_ok=True)
        if update_meta:
            meta = cls._update_meta(folder_root, meta)
        JSONFile.write(path_meta, meta.to_dict())

        return cls(meta)

    @classmethod
    def _update_meta(cls, root: Path, meta: Meta) -> Meta:
        creation_date   = File.get_creation_date(root)
        latest_modified = File.get_child_latest_date_modified(root, exclude_dotfiles=True)

        meta_dict = meta.to_dict()
        meta_dict["date_created"] = meta.date_created or creation_date
        meta_dict["date_modified"] = (
            latest_modified or meta.date_modified or meta_dict["date_created"]
        )

        return Meta.from_dict(meta_dict)


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
            config_allow_overwrite:   bool = False,
            update_folder_meta:       bool = False
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
            config_allow_overwrite
        )
        self.total_rescan(update_meta=update_folder_meta)

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

        if write_new_config:
            # write
            JSONFile.write(
                self._paths.config_json,
                self._config.to_dict()
            )

    def total_rescan(
            self,
            update_meta: bool = False
    ) -> None:
        self._uncache_props()
        self._folders.clear()

        scanned = [
            d for d in os.scandir(self._paths.root)
            if d.is_dir() and not d.name.startswith(".") # only non-dotfile dirs
        ]

        for d in scanned:
            self._folders.append(
                Folder.load(
                    self._paths.root, d.name, self._config,
                    update_meta=update_meta
                )
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

    def add_folders(
            self,
            *folders:        Folder,
            update_meta:     bool = False,
            skip_duplicates: bool = True
    ):
        # ensure no duplicates before add
        if skip_duplicates:
            folders = [f for f in folders if f not in self._folders]
        else:
            for f in folders:
                for f_exist in self._folders:
                    if f == f_exist:
                        raise FileExistsError(f"The folder \"{f.meta.name}\" already exists, and cannot be added again.")

        for f in folders:
            Folder.create(self._paths.root, f.meta, update_meta=update_meta)

        self._uncache_props()
        self._folders.extend(folders)

    def _uncache_props(self):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)