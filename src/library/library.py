# dep

from __future__ import annotations

from functools import cached_property
from pathlib   import Path

import os

from .config  import LibraryConfig, LibraryPaths
from .data    import Meta, Tags
from _util  import FileSystem, JSONFile, SomePath


# folders

class Folder:
    # constr

    def __init__(self, library: Library, meta: Meta):
        self._library   = library
        self._path_root = library.paths.root / meta.data["name"]
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
        return self.meta.data["name"]

    @property
    def path_root(self):
        return self._path_root

    @property
    def path_meta(self):
        return self._path_meta

    # sys

    @property
    def __key(self) -> tuple:
        return self.library, self.name

    def __hash__(self) -> int:
        return hash(self.__key)

    def __eq__(self, other: Folder) -> bool:
        if isinstance(other, Folder):
            return self.__key == other.__key
        return NotImplemented

    # meta

    def meta_refresh(self):
        self._meta = self._meta.get_refreshed(self.path_root)
        JSONFile.write(self.path_meta, self.meta.serialize())


# library

class Library:
    # const

    _UNCACHE_ON_UPDATE = [
        "tags", "folder_relpaths"
    ]

    # constr

    def __init__(
            self,
            library_root: SomePath,
            config: LibraryConfig | None = None,
            *,
            # params:
            config_create_if_missing: bool        = True,
            config_allow_overwrite:   bool        = False,
            do_rescan:                bool        = False,
            folder_skip_if_missing:   bool | None = None,
            folder_create_if_missing: bool        = False
    ):
        self._folders: list[Folder] = []
        self._assign_config_and_paths(
            config,
            Path(library_root)
        )

        config_was_provided = config is not None
        self._init_library(
            config_was_provided      = config_was_provided,
            config_create_if_missing = config_create_if_missing,
            config_allow_overwrite   = config_allow_overwrite
        )

        if do_rescan:
            self.rescan(
                folder_skip_if_missing=(
                    folder_skip_if_missing
                    if folder_skip_if_missing is not None
                    else False
                ),
                folder_create_if_missing=folder_create_if_missing
            )
        else:
            if folder_create_if_missing:
                raise ValueError(
                    "folder_create_if_missing requires do_rescan=True."
                )

            self._rescan_from_cache(
                folder_skip_if_missing=(
                    folder_skip_if_missing
                    if folder_skip_if_missing is not None
                    else True
                )
            )

    def _init_library(
            self, *,
            # params:
            config_was_provided:      bool,
            config_create_if_missing: bool,
            config_allow_overwrite:   bool
    ) -> None:
        try:
            config_found_dict = JSONFile.read(self._paths.config_json)
            config_found = LibraryConfig.from_serialized(config_found_dict)

            if not config_was_provided or config_found == self._config:
                # use existing config
                write_new_config = False
                self._assign_config_and_paths(config_found, self._paths.root)
            elif config_allow_overwrite:
                # delete old config and overwrite
                write_new_config = True
                to_remove = config_found.resolve(self._paths.root)
                to_remove.config_json.unlink() # delete old files
                to_remove.cached_json.unlink(missing_ok=True) # ..
            else:
                raise FileExistsError(
                    f"Attempted to create the configuration file "
                    f"{self._paths.config_json!r} which already exists, "
                    f"but config_allow_overwrite was disabled."
                )
        except FileNotFoundError:
            write_new_config = True # new config if none found
            if not config_create_if_missing:
                raise FileNotFoundError(
                    f"Attempted to load the configuration file "
                    f"{self._paths.config_json!r} which doesn't exist, "
                    f"but config_create_if_missing was disabled."
                )

        if write_new_config: self._write_config()

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
    def folder_relpaths(self) -> list[Path]:
        return sorted([
            Path(f"./{f.name}") for f in self._folders
        ])

    @cached_property
    def tags(self) -> Tags:
        return Tags.combine(*[
            f.meta.data["tags"] for f in self._folders
        ])

    # scanning

    def meta_refresh(self) -> None:
        for f in self._folders:
            f.meta_refresh()
        self._recache(write_cache_json=False) # tags are not in */cache.json

    def rescan(
            self, *,
            # params:
            folder_skip_if_missing:   bool = False,
            folder_create_if_missing: bool = False,
            # sys:
            _recache: bool = True
    ) -> None:
        self._folders.clear()

        folder_names = [
            d.name for d in os.scandir(self._paths.root)
            if d.is_dir() and not d.name.startswith(".") # only non-dotfile dirs
        ]

        self.folders_load(
            *folder_names,

            folder_skip_if_missing=folder_skip_if_missing,
            folder_create_if_missing=folder_create_if_missing,
            _recache=_recache
        )

    def _rescan_from_cache(
            self, *,
            # param(s):
            folder_skip_if_missing: bool = True
    ) -> None:
        if not self.paths.cached_json.is_file():
            return

        folder_names = JSONFile.read(self.paths.cached_json)
        self.folders_load(
            *folder_names,

            folder_skip_if_missing=folder_skip_if_missing,
            folder_create_if_missing=False, # don't try to recreate removed/renamed/etc dirs
            _recache=False
        )

        self._recache(write_cache_json=False)
        # (cached list unchanged except for missing folders, to (mostly) no effect)

    # user-facing folder ops

    def folders_load(
            self, *folder_names: str,
            # params:
            folder_skip_if_missing:   bool = True,
            folder_create_if_missing: bool = False,
            # sys:
            _recache: bool = True
    ) -> None:
        for name in folder_names:
            self._folder_load(
                name,
                folder_skip_if_missing=folder_skip_if_missing,
                folder_create_if_missing=folder_create_if_missing,
                _recache=False # recache once at end
            )
        if _recache: self._recache()

    def folders_create(
            self, *metas: Meta | None,
            # params:
            folder_rename_collisions: bool = True,
            folder_allow_overwrite:   bool = True, # does nothing by default until folder_rename_collisions is disabled
            refresh_meta:             bool = False,
            # sys:
            _recache: bool = True
    ) -> None:
        for meta in metas:
            self._folder_create(
                meta,
                folder_rename_collisions=folder_rename_collisions,
                folder_allow_overwrite=folder_allow_overwrite,
                refresh_meta=refresh_meta,
                _recache=False
            )
        if _recache: self._recache()

    # system folder ops

    def _folders_add_internal(
            self, *folders: Folder,
            # sys:
            _recache: bool = True
    ) -> None:
        self._folders = [
            existing for existing in self._folders
            if existing not in folders
        ]
        self._folders.extend(folders)
        if _recache: self._recache()

    def _folder_load(
            self, folder_name: str, *,
            # params:
            folder_skip_if_missing:   bool,
            folder_create_if_missing: bool,
            # sys:
            _recache: bool = True
    ) -> None:
        # init config
        path_folder = self.paths.root / folder_name
        path_meta   = path_folder / self.config.folder_meta_json

        if path_meta.is_file():
            # meta exists
            meta_raw = JSONFile.read(path_meta)
            meta = Meta.from_serialized(meta_raw)

            # fix potential folder name mismatch
            if meta.data["name"] != folder_name:
                meta = Meta.create(
                    **(meta.data | {"name": folder_name})
                )
                JSONFile.write(path_meta, meta.serialize())

            # init loaded folder
            folder = Folder(self, meta)
        else:
            # meta does not exist
            if folder_skip_if_missing: return
            if not folder_create_if_missing:
                raise FileNotFoundError(
                    f"Attempted to load the folder "
                    f"{folder_name!r} which has no metadata, "
                    f"but folder_skip_if_missing and folder_create_if_missing were disabled."
                )

            # init new folder
            self._folder_create(
                Meta.create(name=folder_name),

                # since no meta exists, renaming is not necessary, and overwrite/refreshing is ok
                folder_rename_collisions=False,
                folder_allow_overwrite=True,
                refresh_meta=True,

                _recache=_recache,
            ); return

        # add folder to internal list
        self._folders_add_internal(
            folder, _recache=_recache
        )

    def _folder_create(
            self, meta: Meta | None, *,
            # params:
            folder_rename_collisions: bool,
            folder_allow_overwrite:   bool,
            refresh_meta:             bool,
            # sys:
            _recache: bool = True
    ) -> None:
        # init config
        meta_not_provided = meta is None
        meta = meta or Meta.create()
        path_folder = self.paths.root / meta.data["name"]

        # handle collisions
        if path_folder.is_dir():
            if folder_rename_collisions:
                # e.g. "Untitled (3)"
                name_valid = FileSystem.make_valid_subdir_name(self.paths.root, meta.data["name"])
                meta = Meta.create(
                    **(meta.data | {"name": name_valid})
                )
                path_folder = self.paths.root / meta.data["name"] # (redefine)
            elif not folder_allow_overwrite:
                raise FileExistsError(
                    f"Attempted to create the folder "
                    f"{meta.data["name"]!r} which already exists, "
                    f"but folder_rename_collisions and folder_allow_overwrite were disabled."
                )

        path_meta = path_folder / self.config.folder_meta_json

        # verify meta nonexistence
        if path_meta.is_file():
            if not folder_allow_overwrite:
                raise FileExistsError(
                    f"Attempted to create the folder "
                    f"{meta.data["name"]!r} which already has metadata, "
                    f"but folder_allow_overwrite was disabled."
                )

        # create folder/meta
        FileSystem.resolve_parents(path_meta)
        if refresh_meta or meta_not_provided:
            meta = meta.get_refreshed(path_folder)
        JSONFile.write(path_meta, meta.serialize())

        # init/add folder to internal list
        folder = Folder(self, meta)
        self._folders_add_internal(
            folder, _recache=_recache
        )


    # util

    def _write_config(self):
        JSONFile.write(
            self._paths.config_json,
            self._config.serialize()
        )

    def _write_cache(self):
        path_strs = [str(p) for p in self.folder_relpaths]
        JSONFile.write(
            self._paths.cached_json, path_strs
        )

    def _recache(self, *, write_cache_json: bool = True):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)
        if write_cache_json:
            self._write_cache()

    def _assign_config_and_paths(
            self,
            config: LibraryConfig | None,
            library_root: Path
    ):
        self._config = config or LibraryConfig.create()
        self._paths = self._config.resolve(library_root)