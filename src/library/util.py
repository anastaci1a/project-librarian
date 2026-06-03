# dep

from __future__ import annotations

from datetime import datetime
from enum     import Enum
from os       import PathLike
from pathlib  import Path
from typing   import Any

import json
import os
import sys


# const

BOX_CHARS_DEFAULT = "─│╭╮╰╯"

type SomePath = str | PathLike[str]


# generic file/folder utils / data collection

class FileData:
    @classmethod
    def make_valid_subdir_name(
            cls,
            parent_dir:       SomePath,
            proposed_name:    str,
            numbering_scheme: str = "%s (%d)"
    ):
        test_name, i = proposed_name, 2
        while (parent_dir / Path(test_name)).is_dir():
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
            FileData.resolve_parents(path)
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


# arg parsing

class ArgParse:
    @staticmethod
    def str_list(arg: str|list[str]|None) -> list[str]|None:
        if isinstance(arg, str): return [arg]
        return arg

    @staticmethod
    def str_or_none(arg: Any) -> str|None:
        if arg is not None: return str(arg)
        return None

    @staticmethod
    def path_or_none(arg: Any) -> Path|None:
        if isinstance(arg, str|PathLike): return Path(arg)
        return None

    @staticmethod
    def datetime_or_none(arg: Any) -> datetime|None:
        if isinstance(arg, str):      return datetime.fromisoformat(arg)
        if isinstance(arg, datetime): return arg
        return None


# cli formatting / displaying

class Ansi(Enum):
    F_RESET     = "\033[0m"
    F_BOLD      = "\033[1m"
    F_ITALIC    = "\033[3m"
    F_UNDERLINE = "\033[4m"

    def __str__(self):
        return self.value

class Cli:
    @staticmethod
    def print_boxed_text(
            text:  str,
            chars: str|None = BOX_CHARS_DEFAULT
    ) -> str|None:
        if chars is None:
            chars = BOX_CHARS_DEFAULT

        if len(chars) != 6: return None # err
        c_hori, c_vert, c_tl, c_tr, c_bl, c_br = chars

        lines = (
            text.strip()
            .replace("\t", " ")
            .replace("\r", "")
            .split("\n")
        )
        max_len = max([len(line) for line in lines])

        top_line = c_tl + (c_hori * (max_len + 2)) + c_tr
        bot_line = c_bl + (c_hori * (max_len + 2)) + c_br

        return "\n".join([
            top_line,
            *[f"{c_vert} {line.ljust(max_len)} {c_vert}" for line in lines],
            bot_line,
        ])

    @staticmethod
    def print_spacer() -> None:
        print("\n\n***\n")

    @staticmethod
    def print_title(
            title: str,
            title_chars: str,
            subtitle: str|None,
            prompt: str
    ) -> None:
        title = f"{Cli.print_boxed_text(title, title_chars)}\n\n"
        subtitle = f"{subtitle}\n\n" if subtitle not in (None, "") else ""

        input(
            f"{Ansi.F_BOLD}{title}{Ansi.F_RESET}"
            f"{Ansi.F_ITALIC}{subtitle}{Ansi.F_RESET}"
            f"{Ansi.F_BOLD}{prompt}{Ansi.F_RESET}"
        )

    @staticmethod
    def print_context(context: str|list[str]) -> None:
        context = ArgParse.str_list(context)
        print(f"{Ansi.F_ITALIC}{"\n".join(context)}{Ansi.F_RESET}")

    @staticmethod
    def print_directive(directive: str|list[str]) -> None:
        directive = ArgParse.str_list(directive)
        print(f"{Ansi.F_BOLD}{"\n".join(directive)}{Ansi.F_RESET}")

    @staticmethod
    def print_list(items: list[str]) -> None:
        i_just = len(f"{len(items)}")
        for i, item in enumerate(items):
            i_str = f"{i+1}.".ljust(i_just+1)
            print(f"{i_str} {item}")

    @staticmethod
    def prompt_list(items: list[str], prompt: str) -> int:
        Cli.print_directive(f"{prompt}\n")
        Cli.print_list(items)
        while True:
            user_input = input("> ")
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(items):
                    return idx
            except ValueError:
                pass