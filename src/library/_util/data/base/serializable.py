# dep

from __future__ import annotations

from abc         import ABC, abstractmethod
from dataclasses import dataclass
from typing      import Any, ClassVar, NotRequired, Required, Self, TypeGuard, TypedDict, \
                        cast, get_args, get_origin, get_type_hints, override

from ...._util.file import JSONFile, SomePath


# typing utils

type JSONPrimitive = None | bool | int | float | str
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]

def is_jsonvalue(value: Any) -> bool:
    if isinstance(value, None | bool | int | float | str):
        return True

    if isinstance(value, list):
        return all(
            is_jsonvalue(item) for item in value
        )

    if isinstance(value, dict):
        return all(
            isinstance(k, str) and is_jsonvalue(v)
            for k, v in value.items()
        )

    return False

def is_serializable_type(obj: Any) -> TypeGuard[type[Serializable[Any]]]:
    return isinstance(obj, type) and issubclass(obj, Serializable)

def get_required_typed_dict_keys(td_type: type) -> frozenset[str]:
    hints = get_type_hints(td_type, include_extras=True)
    total = getattr(td_type, "__total__", True)

    required: set[str] = set()

    for key, hint in hints.items():
        origin = get_origin(hint)

        if origin is NotRequired:
            continue

        if origin is Required:
            required.add(key)
            continue

        if total:
            required.add(key)

    return frozenset(required)


# data

@dataclass(frozen=True)
class Serializable[T](ABC):
    # data

    _DataType: ClassVar[Any] = Any
    _data: T

    # infer T

    def __init_subclass__(
            cls, *,
            baseclass: type|None = None,
            **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)

        baseclass = Serializable if baseclass is None else baseclass

        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)

            if origin is baseclass:
                args = get_args(base)

                if len(args) == 1:
                    cls._DataType = args[0]
                    return

    # constr

    def __init__(
            self, unparsed: Any, /, **kwargs: Any
    ) -> None:
        object.__setattr__(
            self, "_data",
            self._parse(unparsed, **kwargs)
        )

    # prop

    @property
    @abstractmethod
    def data(self) -> T:
        return NotImplementedError

    # parsing

    @classmethod
    def _parse(
            cls, unparsed: Any, /,
            *,
            allow_instances_of_cls: bool = True,
            allow_instances_of_T:   bool = True,
            **kwargs: Any
    ) -> T:
        if allow_instances_of_cls and isinstance(unparsed, cls):
            return unparsed._data

        elif allow_instances_of_T:
            stored_type = cls._DataType
            runtime_type = get_origin(stored_type) or stored_type

            if isinstance(runtime_type, type) and isinstance(unparsed, runtime_type):
                return cast(T, unparsed)

        raise NotImplementedError

    # conversions

    @abstractmethod
    def serialize(self, **kwargs: Any) -> JSONValue:
        raise NotImplementedError

    @classmethod
    def from_serialized(
            cls, serialized: JSONValue, /,
            **kwargs: Any
    ) -> Self:
        return cls(
            cls._validate_serialized(serialized, **kwargs),
            **kwargs
        )

    @classmethod
    def _validate_serialized(
            cls, serialized: JSONValue, /,
            **kwargs: Any
    ) -> JSONValue:
        return serialized

    # file

    def write(self, outfile: SomePath, /, **kwargs: Any) -> None:
        serialized = self.serialize(**kwargs)
        JSONFile.write(outfile, serialized)

    @classmethod
    def read(cls, infile: SomePath, /, **kwargs: Any) -> Self:
        serialized = JSONFile.read(infile)
        return cls.from_serialized(serialized, **kwargs)


# collections

@dataclass(frozen=True)
class SerializableCollection[TD: TypedDict](Serializable[TD], ABC):
    # init (infer TD)

    def __init_subclass__(
            cls, *,
            baseclass: type|None = None,
            **kwargs
    ) -> None:
        baseclass = SerializableCollection if baseclass is None else baseclass

        super().__init_subclass__(
            baseclass=baseclass,
            **kwargs
        )

    # constr

    def __init__(
            self, data_unparsed: dict[str, Any], /,
            **kwargs: Any
    ) -> None:
        super().__init__(data_unparsed, **kwargs)

    # factory

    @classmethod
    def create(
            cls, *,
            ignore_none_args:     bool = True,
            args_defaults: None | dict = None,
            **data_unparsed_args: Any
    ) -> Self:
        if ignore_none_args:
            data_unparsed_args = {
                k: v
                for k, v in data_unparsed_args.items()
                if v is not None
            }

        if args_defaults is not None:
            data_unparsed_args = args_defaults | data_unparsed_args

        return cls(
            data_unparsed_args
        )

    # parsing

    @override
    @classmethod
    def _parse(cls, unparsed: dict[str, Any], /, **kwargs: Any) -> TD:
        if isinstance(unparsed, cls):
            return unparsed._data

        if not isinstance(unparsed, dict):
            raise TypeError(
                f"Expected dict or {cls.__name__}, got {type(unparsed).__name__}"
            )

        hints = get_type_hints(cls._DataType)
        required_keys = get_required_typed_dict_keys(cls._DataType)

        missing = required_keys - unparsed.keys()
        if missing:
            raise TypeError(
                f"Missing required field(s) for {cls.__name__}: {sorted(missing)}"
            )

        data_parsed: dict[str, Any] = {}

        for k, expected_type in hints.items():
            if k not in unparsed:
                continue

            raw_value = unparsed[k]

            data_parsed[k] = cls._parse_raw(
                raw_value,
                expected_type,
                **kwargs
            )

        return cast(TD, data_parsed)

    @classmethod
    def _parse_raw[ExpectedType](
            cls,
            raw_value: Any,
            expected_type: Any,
            /,
            **kwargs: Any
    ) -> ExpectedType:
        # attempt native Serializable parsing
        if is_serializable_type(expected_type):
            return expected_type(raw_value)

        # basic jsonval
        if expected_type is JSONValue:
            if is_jsonvalue(raw_value):
                return cast(ExpectedType, raw_value)

            raise TypeError(
                f"Value {raw_value!r} "
                f"is not JSON-serializable"
            )

        # other expected types
        if isinstance(expected_type, type):
            if isinstance(raw_value, expected_type):
                return cast(ExpectedType, raw_value)

            raise TypeError(
                f"Value {raw_value!r} "
                f"is not an instance of {expected_type!r}"
            )

        # not-expected jsonval
        if is_jsonvalue(raw_value):
            return cast(ExpectedType, raw_value)

        raise TypeError(
            f"Value {raw_value!r} "
            f"cannot be parsed as {expected_type!r}"
        )

    # conversions

    def serialize(self, **kwargs: Any) -> JSONValue:
        hints = get_type_hints(self._DataType)
        data_serialized: dict[str, JSONValue] = {}

        for k, expected_type in hints.items():
            if k not in self._data.keys():
                continue

            raw_value = self._data[k]

            if is_serializable_type(expected_type):
                data_serialized[k] = raw_value.serialize(**kwargs)

            elif is_jsonvalue(raw_value):
                data_serialized[k] = raw_value

            else:
                raise TypeError(
                    f"Field {k!r} cannot be parsed as "
                    f"{JSONValue!s}: {raw_value!r}"
                    f"\n(this shouldn't be possible...)"
                )

        return data_serialized

    @override
    @classmethod
    def _validate_serialized(
            cls, serialized: JSONValue,
            *,
            discard_unknown_fields: bool = True,
            **kwargs: Any
    ) -> dict[str, JSONValue]:
        if not isinstance(serialized, dict):
            raise TypeError(
                f"Expected serialized {cls.__name__} to be a dict, "
                f"got {type(serialized).__name__}"
            )

        expected_keys = get_type_hints(cls._DataType)
        unknown_keys = serialized.keys() - expected_keys.keys()

        if unknown_keys and not discard_unknown_fields:
            raise TypeError(
                f"Unknown field(s) for {cls.__name__}: "
                f"{sorted(unknown_keys)}"
            )

        return {
            k: v for k, v in serialized.items()
            if k in expected_keys
        }