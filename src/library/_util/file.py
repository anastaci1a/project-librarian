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

class File:
    @classmethod
    def make_valid_subdir_name(
            cls,
            parent_dir:       SomePath,
            proposed_name:    str,
            numbering_scheme: str = "%s (%d)"
    ):
        test_name, i = proposed_name, 2
        while (Path(parent_dir) / Path(test_name)).is_dir():
            test_name = numbering_scheme % (proposed_name, i)
            i += 1
        return test_name

    @classmethod
    def resolve_parents(cls, file: SomePath) -> None:
        Path(file).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_creation_date(cls, file: SomePath) -> datetime:
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

    @classmethod
    def get_child_latest_date_modified(
            cls,
            folder: SomePath,
            exclude_dotfiles: bool = True
    ) -> datetime|None:
        scanned = list(os.scandir(folder))
        if exclude_dotfiles:
            scanned = [p for p in scanned if not p.name.startswith(".")]
        ts_latest = max([p.stat().st_mtime for p in scanned], default=None)
        if ts_latest is None:
            return None
        return datetime.fromtimestamp(ts_latest)


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
            File.resolve_parents(path)
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