# dep

from __future__ import annotations

from datetime import datetime
from os       import PathLike
from pathlib  import Path
from typing   import Any

import json
import os
import sys


# const

type SomePath = str | PathLike[str]


# generic file/folder utils / data collection

class FileSystem:
    @classmethod
    def make_valid_subdir_name(
            cls,
            root:             SomePath,
            proposed_name:    str,
            numbering_scheme: str = "%s (%d)"
    ):
        test_name, i = proposed_name, 2
        while (Path(root) / Path(test_name)).is_dir():
            test_name = numbering_scheme % (proposed_name, i)
            i += 1
        return test_name

    @classmethod
    def resolve_parents(cls, file: SomePath) -> None:
        Path(file).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_date_created(cls, file: SomePath) -> datetime:
        stat, ts = Path(file).stat(), None
        if sys.platform == "win32":
            ts = stat.st_ctime
        else:
            try:
                ts = stat.st_birthtime
            except AttributeError:
                ts = stat.st_ctime
        return datetime.fromtimestamp(ts)

    @classmethod
    def get_date_modified(cls, file: SomePath) -> datetime:
        return datetime.fromtimestamp(
            Path(file).stat().st_mtime
        )

    @staticmethod
    def get_earliest_date_modified(paths: list[Path]) -> datetime|None:
        ts_earliest = min(
            (path.stat().st_mtime for path in paths),
            default=None
        )
        if ts_earliest is None:
            return None
        return datetime.fromtimestamp(ts_earliest)

    @staticmethod
    def get_latest_date_modified(paths: list[Path]) -> datetime|None:
        ts_latest = max(
            (path.stat().st_mtime for path in paths),
            default=None
        )
        if ts_latest is None:
            return None
        return datetime.fromtimestamp(ts_latest)

    @classmethod
    def get_children(
            cls,
            root: SomePath,
            *,
            sublevels:        int  = 1,
            include_root:     bool = True,
            exclude_dotfiles: bool = False,
            exclude_folders:  bool = False
    ) -> list[Path]:
        if sublevels < 0:
            raise ValueError("sublevels must be greater than or equal to 0")

        root = Path(root)
        scanned: list[Path] = []

        if sublevels > 0:
            children = [
                path for path in root.iterdir()
                if not exclude_dotfiles or not path.name.startswith(".")
            ]
            subdirs = [path for path in children if path.is_dir()]

            scanned.extend(
                path for path in children
                if not exclude_folders or not path.is_dir()
            )

            if sublevels > 1:
                for subdir in subdirs:
                    scanned.extend(cls.get_children(
                        subdir,
                        sublevels=sublevels - 1,
                        include_root=False,
                        exclude_dotfiles=exclude_dotfiles,
                        exclude_folders=exclude_folders
                    ))

        if include_root:
            scanned.append(root)
        return scanned

# json-specific utils

class JSONFile:
    class _ImmutEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, set):
                return list(o)
            else:
                return super().default(o)

    @staticmethod
    def write(
            outfile:            SomePath,
            json_serializable:  Any,
            create_parent_dirs: bool = True,
            indent:             int  = 2,
            sort_keys:          bool = False
    ) -> str:
        path = Path(outfile)
        if create_parent_dirs:
            FileSystem.resolve_parents(path)
        json_str = json.dumps(
            json_serializable,
            indent=indent,
            sort_keys=sort_keys,
            cls=JSONFile._ImmutEncoder
        )
        with open(path, "w") as file:
            file.write(json_str)
        return json_str

    @staticmethod
    def read(infile: SomePath) -> Any:
        with open(infile, "r") as file:
            json_str = "".join(file.readlines())
        return json.loads(json_str)