# dep

from __future__  import annotations

from dataclasses import replace
from functools   import cached_property
from pathlib     import Path

import os

from .data   import Meta, Tags, TagUtil
from .config import LibraryConfig, LibraryPaths
from .util   import JSONFile, SomePath, FileData


# folders

class Folder:
    # constr

    def __init__(self, path_root: Path, path_meta: Path, meta: Meta):
        self._path_root = path_root
        self._path_meta = path_meta
        self._meta = meta

    # prop

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

    # load (classmethod)

    @classmethod
    def load(
            cls,
            library_root:      Path,
            folder_name:       str,
            config:            LibraryConfig | None = None,
            create_if_missing: bool = True
    ) -> Folder:
        # init config
        library_config = config or LibraryConfig()
        path_folder    = library_root / folder_name
        path_meta      = path_folder / library_config.folder_meta_json

        if not path_meta.is_file():
            # meta does not exist
            if not create_if_missing:
                raise FileNotFoundError(f"Folder \"{folder_name}\" was not found, and create_if_missing is disabled.")
            return cls.create(
                library_root,
                library_config=library_config,
                meta=Meta(
                    name=folder_name
                ),

                # no meta exists, collisions/overwrite is ok
                rename_folder_collisions=False,
                allow_overwrite=True
            )

        # meta exists
        meta_raw = JSONFile.read(path_meta)
        meta = Meta.from_dict(meta_raw)
        return Folder(path_folder, path_meta, meta)

    @classmethod
    def create(
            cls,
            library_root:             Path,
            library_config:           LibraryConfig | None = None,
            meta:                     Meta          | None = None,
            rename_folder_collisions: bool = True,
            allow_overwrite:          bool = False
    ) -> Folder:
        # init config
        meta           = meta or Meta()
        library_config = library_config or LibraryConfig()
        path_folder    = library_root / meta.name

        # handle collisions
        if path_folder.is_dir():
            if rename_folder_collisions:
                # e.g. "Untitled (3)"
                name_valid = FileData.make_valid_subdir_name(library_root, meta.name)
                meta = replace(
                    meta, name=name_valid
                )
                path_folder = library_root / meta.name # (redefine)
            elif not allow_overwrite:
                raise FileExistsError(
                    f"Folder \"{meta.name}\" already exists, and rename_collisions and allow_overwrite are disabled."
                )

        path_meta = path_folder / library_config.folder_meta_json

        # create folder/meta
        if path_meta.is_file():
            if not allow_overwrite:
                raise FileExistsError(
                    f"Folder \"{meta.name}\" already exists, and allow_overwrite is disabled."
                )

        JSONFile.write(path_meta, meta.to_dict())
        return cls(path_folder, path_meta, meta)


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
        self.folders_rescan(update_meta=update_folder_meta)

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

    # <folder>.* mut

    def folders_rescan(
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
                    self._paths.root, d.name, self._config
                )
            )

    def meta_refresh(self) -> None:
        self._uncache_props()

        for f in self._folders:
            f.meta_refresh()

    # self.* mut

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

        # # this process makes less sense now that
        # # Folder instances must be associated with
        # # a Library instance to begin with
        # for f in folders:
        #     new_folder = Folder.create(
        #         self._paths.root,
        #         self._config,
        #         meta=f.meta
        #     )
        #     self._folders.append(new_folder)

        self._folders.extend(folders)
        self._uncache_props()

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