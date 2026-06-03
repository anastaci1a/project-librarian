# dep

from __future__  import annotations

from dataclasses import replace
from functools   import cached_property
from pathlib     import Path

import os

from .config import LibraryConfig, LibraryPaths
from .data   import Meta, Tags, TagUtil
from .util   import FileData, JSONFile, SomePath


# folders

class Folder:
    # constr

    def __init__(self, library: Library, meta: Meta):
        self._library   = library
        self._path_root = library.paths.root / meta.name
        self._path_meta = self._path_root / library.config.folder_meta_json
        self._meta      = meta

    # prop

    @property
    def library(self):
        return self._library

    @property
    def meta(self):
        return self._meta

    @property
    def name(self):
        return self.meta.name

    @property
    def path_root(self):
        return self._path_root

    @property
    def path_meta(self):
        return self._path_meta

    # sys

    def __eq__(self, other: Folder) -> bool:
        if isinstance(other, Folder):
            return self.meta.name == other.meta.name
        return NotImplemented

    # meta

    def meta_refresh(self, overwrite: bool = True):
        self._meta = self._meta.get_refreshed(self.path_root)
        if overwrite:
            pass

    # load/create

    @classmethod
    def load(
            cls,
            library:     Library,
            folder_name: str,
            # ..
            create_if_missing: bool = True
    ) -> Folder:
        # init config
        path_folder = library.paths.root / folder_name
        path_meta   = path_folder / library.config.folder_meta_json

        if not path_meta.is_file():
            # meta does not exist
            if not create_if_missing:
                raise FileNotFoundError(f"Folder \"{folder_name}\" was not found, and create_if_missing is disabled.")
            # create new meta
            return cls.create(
                library, Meta(name=folder_name),

                # since no meta exists, renaming is not necessary, overwrite/refreshing is ok
                rename_folder_collisions=False,
                allow_overwrite=True,
                refresh_meta=True
            )

        # meta exists
        meta_raw = JSONFile.read(path_meta)
        meta = Meta.from_dict(meta_raw)
        return Folder(library, meta)

    @classmethod
    def create(
            cls,
            library: Library,
            meta:    Meta | None = None,
            # ..
            rename_folder_collisions: bool = True,
            allow_overwrite:          bool = False,
            refresh_meta:             bool = False
    ) -> Folder:
        # init config
        meta_not_provided = meta is None
        meta = meta or Meta()
        path_folder = library.paths.root / meta.name

        # handle collisions
        if path_folder.is_dir():
            if rename_folder_collisions:
                # e.g. "Untitled (3)"
                name_valid = FileData.make_valid_subdir_name(library.paths.root, meta.name)
                meta = replace(
                    meta, name=name_valid
                )
                path_folder = library.paths.root / meta.name # (redefine)
            elif not allow_overwrite:
                raise FileExistsError(
                    f"Folder \"{meta.name}\" already exists, and rename_collisions and allow_overwrite are disabled."
                )

        path_meta = path_folder / library.config.folder_meta_json

        # create folder/meta
        if path_meta.is_file():
            if not allow_overwrite:
                raise FileExistsError(
                    f"Folder \"{meta.name}\" already exists, and allow_overwrite is disabled."
                )

        FileData.resolve_parents(path_meta)
        if refresh_meta or meta_not_provided:
            meta = meta.get_refreshed(path_folder)
        JSONFile.write(path_meta, meta.to_dict())
        return cls(library, meta)


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
            config: LibraryConfig | None = None,

            scan_folders:                  bool = True,
            config_create_if_missing:      bool = True,
            config_allow_overwrite:        bool = False
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

        if scan_folders:
            self.folders_rescan(
                # create_if_missing=True # (default)
            )

    # main props

    @property
    def config(self) -> LibraryConfig:
        return self._config

    @property
    def paths(self) -> LibraryPaths:
        return self._paths

    @property
    def folders(self) -> list[Folder]:
        return self._folders.copy()

    # computed props

    @cached_property
    def folder_paths(self) -> list[Path]:
        return [
            f.path_root for f in self._folders
        ]

    @cached_property
    def tags(self) -> Tags:
        return TagUtil.combine(*[
            f.meta.tags for f in self._folders
        ])

    # filesystem

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

    # <folder>.* mut

    def meta_refresh(self) -> None:
        self._uncache_props()

        for f in self._folders:
            f.meta_refresh()

    # self.* mut

    def folders_rescan(self, create_if_missing: bool = True) -> None:
        self._uncache_props()
        self._folders.clear()

        scanned = [
            d for d in os.scandir(self._paths.root)
            if d.is_dir() and not d.name.startswith(".") # only non-dotfile dirs
        ]

        for d in scanned:
            self._folders.append(
                Folder.load(
                    self, d.name,
                    create_if_missing=create_if_missing
                )
            )

    def add_folders(
            self,
            *folders:        Folder,
            skip_duplicates: bool = True
    ):
        # ensure no duplicates before add
        if skip_duplicates:
            folders = [f for f in folders if f not in self._folders]
        else:
            for f in folders:
                if f in self._folders:
                    raise FileExistsError(f"Folder \"{f.meta.name}\" already exists, and cannot be added again.")

        self._folders.extend(folders)
        self._uncache_props()

        ### the below process makes less sense now that Folder instances
        ### must be associated with a Library instance to begin with, so
        ### reinstantiation is not necessary anymore

        # for f in folders:
        #     new_folder = Folder.create(
        #         self._paths.root,
        #         self._config,
        #         meta=f.meta
        #     )
        #     self._folders.append(new_folder)

        ### TODO: this entire function is not really needed tbh, I more need copy/move_folders

    # util

    def _assign_config_and_paths(
            self,
            config: LibraryConfig | None,
            library_root: Path
    ):
        self._config = config or LibraryConfig()
        self._paths = self._config.resolve(library_root)

    def _uncache_props(self):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)