from __future__ import annotations

import os
import shutil

from functools import cached_property
from pathlib   import Path

from ._util       import FileSystem, Generator, JSONFile, SomePath
from ._util.state import requires_active
from .config      import LibraryConfig, LibraryPaths
from .data        import Meta, Tags
from .folder      import Folder


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
            config_create_if_missing: bool = True,
            config_allow_overwrite:   bool = False,
            load_cache:               bool = True
    ):
        self._is_active = False
        self._folders: dict[str, Folder] = {}
        self._config = config or LibraryConfig.create()
        self._paths = self._config.resolve(library_root)

        config_was_provided = config is not None
        self._init_library(
            config_was_provided      = config_was_provided,
            config_create_if_missing = config_create_if_missing,
            config_allow_overwrite   = config_allow_overwrite
        )
        self._is_active = True

        if load_cache:
            self.load_cache()

    def _init_library(
            self, *,
            # params:
            config_was_provided:      bool,
            config_create_if_missing: bool,
            config_allow_overwrite:   bool
    ) -> None:
        try:
            config_found_dict = JSONFile.read(self._paths.config_json)
            config_found = LibraryConfig.deserialize(config_found_dict)

            if not config_was_provided or config_found == self._config:
                # use existing config
                write_new_config = False
                self._config = config_found
                self._paths = self._config.resolve(self._paths.root)
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
    def is_active(self) -> bool:
        return self._is_active

    @property
    def config(self) -> LibraryConfig:
        return self._config

    @property
    def paths(self) -> LibraryPaths:
        return self._paths

    @property
    def folders(self) -> dict[str, Folder]:
        return self._folders.copy()

    # computed props

    @cached_property
    def folder_relpaths(self) -> list[Path]:
        return sorted([
            Path(f"./{f.name}") for f in self._folders.values()
        ])

    @cached_property
    def tags(self) -> Tags:
        return Tags.combine(*[
            f.meta.data["tags"] for f in self._folders.values()
        ])

    # scanning

    @requires_active
    def meta_refresh(self) -> None:
        for f in self._folders.values():
            f.meta_refresh()
        self._recache(write_cache_json=False) # tags are not in */cache.json

    @requires_active
    def rescan(
            self, *,
            # params:
            folder_skip_if_incompatible:   bool = False,
            folder_skip_if_missing:        bool = False,
            folder_create_if_missing:      bool = True,
            folder_fill_missing_fields:    bool = True,
            folder_discard_unknown_fields: bool = True,
            # sys:
            _recache: bool = True
    ) -> None:
        self.folders_detach(_recache=False)

        folder_names = [
            d.name for d in os.scandir(self.paths.root)
            if d.is_dir() and not d.name.startswith(".") # only non-dotfile dirs
        ]

        self.folders_load(
            *folder_names,

            folder_skip_if_incompatible=folder_skip_if_incompatible,
            folder_skip_if_missing=folder_skip_if_missing,
            folder_create_if_missing=folder_create_if_missing,
            folder_fill_missing_fields=folder_fill_missing_fields,
            folder_discard_unknown_fields=folder_discard_unknown_fields,
            _recache=_recache
        )

    @requires_active
    def load_cache(
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
            _recache=True
        )

        self._recache(write_cache_json=False)
        # (cached list unchanged except for missing folders, to (mostly) no effect)

    # destructive ops

    @requires_active
    def folders_detach(self, *, _recache: bool = True) -> None:
        try:
            for folder in set(self._folders.values()):
                # noinspection PyProtectedMember
                folder._deactivate()
                self._folders.pop(folder.uid)
        finally:
            if _recache: self._recache()

    @requires_active
    def folders_purge(self, *, _recache: bool = True) -> None:
        try:
            for folder in set(self._folders.values()):
                folder.data_delete()
                self._folders.pop(folder.uid)
        finally:
            if _recache: self._recache()

    @requires_active
    def purge_all(self) -> None:
        path_data = self.paths.config_json.parent
        if (
                path_data == self.paths.root
                or not path_data.is_relative_to(self.paths.root)
        ):
            raise ValueError(
                f"Refusing to purge library data at {path_data!r} because "
                f"it is not a dedicated directory inside {self.paths.root!r}."
            )

        try:
            self.folders_purge(_recache=False)
            if path_data.exists():
                shutil.rmtree(path_data)
        finally:
            self._is_active = False

    # folder ops

    @requires_active
    def folders_load(
            self, *folder_names: str,
            # params:
            folder_skip_if_incompatible:   bool = False,
            folder_skip_if_missing:        bool = False,
            folder_create_if_missing:      bool = True,
            folder_fill_missing_fields:    bool = False,
            folder_discard_unknown_fields: bool = False,
            # sys:
            _recache: bool = True
    ) -> set[Folder]:
        succeeded: list[Folder] = []
        try:
            for name in set(folder_names):
                folder = self._folder_load(
                    name,
                    folder_skip_if_incompatible=folder_skip_if_incompatible,
                    folder_skip_if_missing=folder_skip_if_missing,
                    folder_create_if_missing=folder_create_if_missing,
                    folder_fill_missing_fields=folder_fill_missing_fields,
                    folder_discard_unknown_fields=folder_discard_unknown_fields,
                    _recache=False # recache once at end
                )
                if folder is not None:
                    succeeded.append(folder)
        finally:
            if _recache: self._recache()
        return set(succeeded)

    @requires_active
    def folders_create(
            self, *metas: Meta | None,
            # params:
            folder_skip_collisions:   bool = False, # overrides all other collision handling
            folder_rename_collisions: bool = True,
            folder_allow_overwrite:   bool = True, # does nothing by default until folder_rename_collisions is disabled
            refresh_meta:             bool = False,
            # sys:
            _recache: bool = True
    ) -> set[Folder]:
        succeeded: list[Folder] = []
        try:
            for meta in metas:
                folder = self._folder_create(
                    meta,
                    folder_skip_collisions=folder_skip_collisions,
                    folder_rename_collisions=folder_rename_collisions,
                    folder_allow_overwrite=folder_allow_overwrite,
                    refresh_meta=refresh_meta,
                    _recache=False
                )
                if folder is not None:
                    succeeded.append(folder)
        finally:
            if _recache: self._recache()
        return set(succeeded)

    # system folder ops

    def _folders_add_internal(
            self, *folders: Folder,
            # sys:
            _recache: bool = True
    ) -> None:
        uids = [folder.uid for folder in folders]

        if len(uids) != len(set(uids)):
            raise ValueError("Duplicate UIDs in folders being added.")

        collisions = self._folders.keys() & set(uids)
        if collisions:
            raise ValueError(f"Folder UIDs already loaded: {collisions!r}")

        self._folders.update(zip(uids, folders))

        if _recache:
            self._recache()

    def _folders_remove_internal(
            self, *folders: Folder,
            # sys:
            _recache: bool = True
    ) -> None:
        uids = {folder.uid for folder in folders}

        invalid = uids - self._folders.keys()
        if len(invalid) > 0:
            raise ValueError(f"UIDs of folders to remove are not in library: {invalid!r}")

        for uid in uids:
            # noinspection PyProtectedMember
            self._folders.get(uid)._deactivate()
            self._folders.pop(uid)
        if _recache: self._recache()

    def _folder_load(
            self, folder_name: str, *,
            # params:
            folder_skip_if_incompatible:   bool,
            folder_skip_if_missing:        bool,
            folder_create_if_missing:      bool,
            folder_fill_missing_fields:    bool,
            folder_discard_unknown_fields: bool,
            # sys:
            _recache: bool = True
    ) -> Folder | None:
        # init config
        path_folder = self.paths.root / folder_name
        path_meta   = path_folder / self.config.folder_meta_json

        if path_meta.is_file():
            # meta exists
            meta_raw = JSONFile.read(path_meta)
            try:
                meta = Meta.deserialize(
                    meta_raw,
                    discard_unknown_fields=folder_discard_unknown_fields,
                    repair_with_defaults=folder_fill_missing_fields,
                    uid_generator=self._uid_generate
                )
            except TypeError:
                if folder_skip_if_incompatible:
                    return None
                raise
            meta_changed = folder_fill_missing_fields

            # fix potential folder/meta name mismatch
            if meta.data["name"] != folder_name:
                meta = Meta.create(
                    **(meta.data | {"name": folder_name})
                )
                meta_changed = True

            # overwrite meta if changed internally
            if meta_changed:
                meta.write(path_meta)

            # init loaded folder
            folder = Folder(meta, path_folder, path_meta)
        else:
            # meta does not exist
            if folder_skip_if_missing: return None
            if not folder_create_if_missing:
                raise FileNotFoundError(
                    f"Attempted to load the folder "
                    f"{folder_name!r} which has no metadata, "
                    f"but folder_skip_if_missing and folder_create_if_missing were disabled."
                )

            # init new folder
            return self._folder_create(
                Meta.create(name=folder_name, uid_generator=self._uid_generate),

                # since no meta exists, renaming is not necessary, and overwrite/refreshing is ok
                folder_skip_collisions=False,
                folder_rename_collisions=False,
                folder_allow_overwrite=True,
                refresh_meta=True,

                _recache=_recache,
            )

        # add folder to internal list
        self._folders_add_internal(
            folder, _recache=_recache
        )
        return folder

    def _folder_create(
            self, meta: Meta | None, *,
            # params:
            folder_skip_collisions:   bool,
            folder_rename_collisions: bool,
            folder_allow_overwrite:   bool,
            refresh_meta:             bool,
            # sys:
            _recache: bool = True
    ) -> Folder | None:
        # init config
        meta_not_provided = meta is None
        meta = meta or Meta.create(uid_generator=self._uid_generate)
        path_folder = self.paths.root / meta.data["name"]

        # handle collisions
        if path_folder.is_dir():
            if folder_skip_collisions:
                return None
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
        meta.write(path_meta)

        # init/add folder to internal list
        folder = Folder(meta, path_folder, path_meta)
        self._folders_add_internal(
            folder, _recache=_recache
        )
        return folder

    # util

    def _uid_generate(self):
        return Generator.uid_generate(
            self.config.folder_uid_len,
            exclude=self._folders.keys()
        )

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

    def _require_active(self) -> None:
        if not self.is_active:
            raise RuntimeError(
                "This Library instance is no longer active."
            )

    def _recache(self, *, write_cache_json: bool = True):
        for d in Library._UNCACHE_ON_UPDATE:
            self.__dict__.pop(d, None)
        if write_cache_json:
            self._write_cache()
