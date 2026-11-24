# dep

from datetime import datetime
from collections.abc import Mapping
from os       import PathLike
from pathlib  import Path
from types    import UnionType
from typing   import Any, TypeAliasType, TypeGuard, TypeVar, get_origin, get_args, Union

# noinspection PyUnresolvedReferences
from typing_extensions import TypeForm


def bind_type(hint: Any, bindings: Mapping[Any, Any]) -> Any:
    """Substitute free parameters in a class, alias, union, or generic expression."""
    if isinstance(hint, TypeVar):
        return bindings.get(hint, hint)
    parameters = getattr(hint, "__parameters__", ())
    if parameters:
        return hint[tuple(bindings.get(param, param) for param in parameters)]
    return hint


def _matches_type(obj: Any, hint: Any, active: set[tuple[int, Any]]) -> bool:
    if hint is Any:
        return True
    if hint is None:
        return obj is None

    origin = get_origin(hint)
    args = get_args(hint)
    alias = origin if isinstance(origin, TypeAliasType) else hint
    if isinstance(alias, TypeAliasType):
        # A recursive alias can revisit a shared value, but not on its active path.
        key = (id(obj), hint)
        if key in active:
            return False
        if len(alias.__type_params__) != len(args):
            raise TypeError(f"Expected type arguments for {alias}")
        bindings = dict(zip(alias.__type_params__, args))
        active.add(key)
        try:
            return _matches_type(obj, bind_type(alias.__value__, bindings), active)
        finally:
            active.remove(key)

    if origin in (UnionType, Union):
        return any(_matches_type(obj, member, active) for member in args)
    if origin in (list, set, frozenset) and len(args) == 1:
        return isinstance(obj, origin) and all(_matches_type(item, args[0], active) for item in obj)
    if origin in (dict, Mapping) and len(args) == 2:
        return isinstance(obj, origin) and all(
            _matches_type(key, args[0], active) and _matches_type(value, args[1], active)
            for key, value in obj.items()
        )
    if origin is tuple:
        if not isinstance(obj, tuple):
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_matches_type(item, args[0], active) for item in obj)
        return len(obj) == len(args) and all(
            _matches_type(item, arg, active) for item, arg in zip(obj, args)
        )
    if origin is PathLike and len(args) == 1:
        return isinstance(obj, PathLike) and _matches_type(obj.__fspath__(), args[0], active)
    if isinstance(hint, type):
        return isinstance(obj, hint)
    raise TypeError(f"Unsupported type expression: {hint!r}")


# arg parsing

class ArgParse:
    # parse

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

    # verif

    @staticmethod
    def is_type[T](obj: object, stored_type: TypeForm[T], /) -> TypeGuard[T]:
        return _matches_type(obj, stored_type, set())
