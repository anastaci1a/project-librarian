# dep

from abc         import ABC
from dataclasses import dataclass, fields, is_dataclass
from types       import UnionType, get_original_bases
from typing      import Any, ClassVar, Self, TypeGuard, cast, get_args, get_origin, get_type_hints, Union, override

from .base    import Serializable
from ...file  import JSONValue
from ...parse import ArgParse, bind_type


# value

@dataclass(frozen=True, init=False)
class SerializableValue[Input, Data](Serializable, ABC):
    # runtime types

    _InputType: ClassVar[Any]
    _DataType:  ClassVar[Any]

    # prop

    _data: Data

    @property
    def data(self) -> Data:
        return self._data

    # init

    def __init_subclass__(
            cls, *,
            baseclass: type | None = None,
            **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)

        for base in get_original_bases(cls):
            parent = get_origin(base) or base
            if not isinstance(parent, type) or not issubclass(parent, SerializableValue):
                continue
            if baseclass is not None and parent is not baseclass:
                continue

            args = get_args(base)
            parameters = getattr(parent, "__parameters__", ())

            if parameters and not args:
                raise TypeError(f"{cls.__name__} must specialize {parent.__name__}")
            if parent is SerializableValue:
                cls._InputType, cls._DataType = args
            else:
                bindings = dict(zip(parameters, args, strict=True))
                # noinspection PyProtectedMember
                cls._InputType = bind_type(parent._InputType, bindings)
                # noinspection PyProtectedMember
                cls._DataType = bind_type(parent._DataType, bindings)
            return
        raise TypeError(f"No SerializableValue base found for {cls.__name__}")

    def __init__(self, unparsed: Input | Self, /) -> None:
        if isinstance(unparsed, type(self)):
            parsed = unparsed._data
        else:
            parsed = self._parse(cast(Input, unparsed))

        object.__setattr__(self, "_data", parsed)

    # serial

    @override
    @classmethod
    def deserialize(cls, serialized: JSONValue, /) -> Self:
        """Convert `JSONValue` to `Input` type, parse, and initialize"""
        if cls._is_input_type(serialized):
            return cls(serialized)

        raise TypeError(
            f"{cls.__name__} cannot parse "
            f"{type(serialized).__name__}: {serialized!r}"
        )

    # parse

    @classmethod
    def _parse(cls, unparsed: Input, /) -> Data:
        """Parse from `Input` type to `Data` type"""
        if cls._is_data_type(unparsed):
            return unparsed

        raise TypeError(
            f"{cls.__name__} cannot parse "
            f"{type(unparsed).__name__}: {unparsed!r}"
        )

    # typing util

    @classmethod
    def _is_input_type(cls, obj: object, /) -> TypeGuard[Input]:
        return ArgParse.is_type(obj, cls._InputType)

    @classmethod
    def _is_data_type(cls, obj: object, /) -> TypeGuard[Data]:
        return ArgParse.is_type(obj, cls._DataType)


# model

class SerializableModel(Serializable):
    # serial

    @override
    def serialize(self, /) -> dict[str, JSONValue]:
        if not is_dataclass(self):
            raise TypeError("SerializableModel subclasses must be dataclasses")

        result = {}
        # noinspection PyDataclass, PyTypeChecker
        for f in fields(self):
            if not f.init:
                continue
            value = getattr(self, f.name)
            if value is not None or not f.metadata.get("omit_none"):
                result[f.name] = _encode(value)

        return result

    @classmethod
    @override
    def deserialize(cls, serialized: JSONValue, /, *, discard_unknown_fields: bool = True) -> Self:
        # noinspection PyArgumentList
        return cls(
            **cls._decode_fields(
                serialized,
                discard_unknown_fields=discard_unknown_fields
            )
        )

    # util

    @classmethod
    def _decode_fields(cls, value: JSONValue, /, *, discard_unknown_fields: bool) -> dict[str, Any]:
        if not is_dataclass(cls) or not isinstance(value, dict):
            raise TypeError(f"Expected a JSON object for dataclass {cls.__name__}")
        if not all(isinstance(key, str) for key in value):
            raise TypeError(f"{cls.__name__} expects string field names")

        hints = get_type_hints(cls)
        # noinspection PyDataclass, PyTypeChecker
        names = {f.name for f in fields(cls) if f.init}
        unknown = value.keys() - names

        if unknown and not discard_unknown_fields:
            raise TypeError(f"Unknown field(s) for {cls.__name__}: {sorted(unknown)}")
        return {k: _decode(hints[k], v, f"{cls.__name__}.{k}") for k, v in value.items() if k in names}


# model utils

def _encode(value: Any, /) -> JSONValue:
    if isinstance(value, Serializable):
        return value.serialize()
    if isinstance(value, (list, tuple)):
        return [_encode(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, (str, int, float, type(None))):
        return value
    raise TypeError(f"Cannot encode {value!r} as JSON")

def _decode(hint: Any, value: JSONValue, path: str, /) -> Any:
    origin, args = get_origin(hint), get_args(hint)
    if hint is JSONValue and ArgParse.is_type(value, JSONValue):
        return value
    if origin in (Union, UnionType) and len(args) == 2 and type(None) in args:
        inner = next(arg for arg in args if arg is not type(None))
        return None if value is None else _decode(inner, value, path)
    if isinstance(hint, type) and issubclass(hint, Serializable):
        try:
            return hint.deserialize(value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{path}: {error}") from error
    if origin is dict and len(args) == 2 and args[0] is str and isinstance(value, dict):
        if all(isinstance(key, str) for key in value):
            return {k: _decode(args[1], v, f"{path}[{k!r}]") for k, v in value.items()}
    if isinstance(value, list):
        if origin is list and len(args) == 1:
            return [_decode(args[0], v, f"{path}[{i}]") for i, v in enumerate(value)]
        if origin is tuple:
            if len(args) == 2 and args[1] is Ellipsis:
                return tuple(_decode(args[0], v, f"{path}[{i}]") for i, v in enumerate(value))
            if len(value) == len(args):
                return tuple(_decode(t, value[i], f"{path}[{i}]") for i, t in enumerate(args))
    if hint in (str, int, float, bool, type(None)) and type(value) is hint:
        return value
    raise TypeError(f"{path}: expected {hint}, got {value!r}")
