# dep

from __future__ import annotations

from abc         import ABC, abstractmethod
from dataclasses import dataclass
from typing      import Any, ClassVar, Self, TypedDict, TypeGuard, cast, get_type_hints, override

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


# data

@dataclass(frozen=True)
class Serializable[T](ABC):
    # prop

    _data: T

    # constr

    def __init__(
            self, unparsed: Any, /, **kwargs: Any
    ) -> None:
        self.__dict__["_data"] = self._parse(
            unparsed, **kwargs
        )

    # prop

    @property
    def data(self) -> T:
        return self._data # unsafe by default

    # parsing

    @classmethod
    def _parse(
            cls, unparsed: Any, /, **kwargs: Any
    ) -> T:
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
            serialized,
            **kwargs
        )

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
class SerializableCollection[DataTypes: TypedDict](Serializable[DataTypes], ABC):
    # const

    _DataTypes: ClassVar[type[Any]]

    # constr

    def __init__(
            self, data_unparsed: dict[str, Any], /,
            **kwargs: Any
    ) -> None:
        super().__init__(data_unparsed, **kwargs)

    # factory

    @classmethod
    def create(
            cls, **data_unparsed_args: Any
    ) -> Self:
        # if ignore_none_args:
        data_unparsed_args = {
            k: v
            for k, v in data_unparsed_args.items()
            if v is not None # TODO: missing key behavior (1)
        }
        return cls(
            data_unparsed_args
        )

    # parsing

    @override
    @classmethod
    def _parse(cls, data_unparsed: dict[str, Any], /, **kwargs: Any) -> DataTypes:
        hints = get_type_hints(cls._DataTypes)
        data_parsed: dict[str, Any] = {}

        for k, expected_type in hints.items():
            if k not in data_unparsed:
                continue # TODO: missing key behavior (2)

            raw_value = data_unparsed[k]

            try:
                data_parsed[k] = cls._parse_raw(
                    raw_value, expected_type, **kwargs
                )
            except TypeError:
                raise TypeError(
                    f"Field {k!r} cannot be parsed as "
                    f"{JSONValue!s}: {raw_value!r}"
                )

        return cast(DataTypes, data_parsed)

    @classmethod
    def _parse_raw[ExpectedType](
            cls, raw_value: Any,
            expected_type: type[ExpectedType],
            /, **kwargs: Any
    ) -> ExpectedType:
        if is_serializable_type(expected_type):
            if isinstance(raw_value, expected_type):
                return raw_value
            else:
                return cast(
                    ExpectedType,
                    expected_type.from_serialized(raw_value)
                )

        if is_jsonvalue(raw_value):
            return raw_value

        raise TypeError(
            f"Value {raw_value!r} cannot be parsed as {ExpectedType!r}"
        )


    # conversions

    def serialize(self, **kwargs: Any) -> JSONValue:
        hints = get_type_hints(self._DataTypes)
        data_serialized: dict[str, JSONValue] = {}

        for k, expected_type in hints.items():
            if k not in self.data.keys():
                continue # TODO: missing key behavior (3)

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