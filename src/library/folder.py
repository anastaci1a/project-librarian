# dep

from __future__ import annotations

from pathlib import Path

from ._util       import FileSystem, JSONFile
from ._util.state import requires_active

from .data        import Meta


# folder

class Folder:
    # constr

    def __init__(self, meta: Meta, path_root: Path, path_meta: Path):
        self._is_active: bool = True
        self._meta:      Meta = meta
        self._path_root: Path = path_root
        self._path_meta: Path = path_meta

    # prop

    @property
    def is_active(self):
        return self._is_active

    @property
    def meta(self):
        return self._meta

    @property
    def uid(self):
        return self.meta.uid

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

    @property
    def __key(self) -> tuple:
        return self.uid, self.name, self.path_root, self.path_meta

    def __hash__(self) -> int:
        return hash(self.__key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Folder):
            return self.__key == other.__key
        return NotImplemented

    def _require_active(self) -> None:
        if not self.is_active:
            raise RuntimeError(
                "This Folder instance is no longer active."
            )

    def _deactivate(self) -> None:
        self._is_active = False

    # meta

    @requires_active
    def meta_reset(self) -> None:
        self._meta = self._meta.get_reset()
        self._meta_write()

    @requires_active
    def meta_refresh(self) -> None:
        self._meta = self._meta.get_refreshed(self.path_root)
        self._meta_write()

    @requires_active
    def _meta_write(self) -> None:
        JSONFile.write(self.path_meta, self.meta.serialize())

    # data

    @requires_active
    def data_delete(self) -> None:
        FileSystem.remove_data_file(self.path_root, self.path_meta)
        self._is_active = False
