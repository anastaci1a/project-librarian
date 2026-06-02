# dep

from __future__  import annotations
from dataclasses import dataclass
from functools import cached_property

from .data import Meta, Tags, TagUtil


# export

@dataclass
class Folder:
    meta: Meta

class Library:
    _UNCACHE_ON_UPDATE = [
        "tags", "folder_paths"
    ]

    # constr

    def __init__(self):
        self._folders: list[Folder] = []

    # get

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