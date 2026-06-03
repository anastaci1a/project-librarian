# dep

from datetime import datetime
from os       import PathLike
from pathlib  import Path
from typing   import Any


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