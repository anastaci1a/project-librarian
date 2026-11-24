# dep

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib     import Path
import os

from ._util           import SomePath
from ._util.data      import SerializablePath
from ._util.data.serializable import SerializableModel


# library config

@dataclass(frozen=True, kw_only=True)
class LibraryConfig(SerializableModel):
    config_json: SerializablePath = SerializablePath(".library/config.json")
    cached_json: SerializablePath = SerializablePath(".library/cached.json")
    folder_meta_json: SerializablePath = SerializablePath(".folder/meta.json")
    folder_uid_len: int = field(default=16, compare=False)

    def resolve(self, library_root: SomePath) -> LibraryPaths:
        paths = LibraryPaths(Path(library_root), self)
        if paths.config_json.resolve() == paths.cached_json.resolve():
            raise ValueError("Library configuration and cache must use separate files")
        return paths


# paths

def _child_path(root: Path, relative: SomePath) -> Path:
    part = Path(relative)
    reserved = os.name == "nt" and any(os.path.isreserved(p) for p in part.parts)
    if not part.parts or part.anchor or ".." in part.parts or reserved:
        raise ValueError(f"Expected a relative path inside {root}: {part}")
    path = root / part
    if root.resolve() not in path.resolve().parents:
        raise ValueError(f"Path leaves {root}: {part}")
    return path


@dataclass(frozen=True)
class LibraryPaths:
    root:   Path
    config: LibraryConfig

    @property
    def config_json(self) -> Path:
        return _child_path(self.root, self.config.config_json)

    @property
    def cached_json(self) -> Path:
        return _child_path(self.root, self.config.cached_json)

    def folder_root(self, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError(f"Expected a single folder name: {name!r}")
        return _child_path(self.root, name)

    def folder_meta_json(self, folder_root: SomePath) -> Path:
        return _child_path(Path(folder_root), self.config.folder_meta_json)
