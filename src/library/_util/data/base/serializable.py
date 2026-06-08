# dep

from __future__ import annotations

from abc         import ABC, abstractmethod
from dataclasses import dataclass
from typing      import Any, ClassVar, Self, TypedDict, Unpack, cast, get_type_hints

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

def is_serializable(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, Serializable)


# data

@dataclass(frozen=True)
class Serializable[T](ABC):
    # prop

    _data: T

    # constr

    def __init__(self, unparsed: Any, **kwargs: Any) -> None:
        self.__dict__["_data"] = self._parse(unparsed, **kwargs)

    # prop

    @property
    def data(self) -> T:
        return self._data # unsafe by default

    # parsing

    @classmethod
    @abstractmethod
    def _parse(cls, unparsed: Any, **kwargs: Any) -> T:
        raise NotImplementedError

    # conversions

    @abstractmethod
    def serialize(self, **kwargs: Any) -> JSONValue:
        raise NotImplementedError

    @classmethod
    def from_serialized(cls, serialized: JSONValue, **kwargs: Any) -> Self:
        return cls(serialized, **kwargs)

    # file

    def write(self, outfile: SomePath, **kwargs: Any) -> None:
        serialized = self.serialize(**kwargs)
        JSONFile.write(outfile, serialized)

    @classmethod
    def read(cls, infile: SomePath, **kwargs: Any) -> Self:
        serialized = JSONFile.read(infile)
        return cls.from_serialized(serialized, **kwargs)


# collections

@dataclass(frozen=True)
class SerializableCollection[ArgTypes: TypedDict](Serializable[ArgTypes], ABC):
    # const

    _ArgTypes: ClassVar[type[Any]]

    # constr

    def __init__(self, data_unparsed: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(data_unparsed, **kwargs)

    # factory

    @classmethod
    def create(cls, **data_unparsed_args: Any) -> Self:
        return cls(data_unparsed_args)

    # parsing

    @classmethod
    def _parse(cls, data_unparsed: dict[str, Any], **kwargs: Any) -> ArgTypes:
        hints = get_type_hints(cls._ArgTypes)
        data_parsed: dict[str, Any] = {}

        for k, expected_type in hints.items():
            if k not in data_unparsed:
                raise KeyError(
                    f"Missing required key: {k!r}"
                )

            raw_value = data_unparsed[k]

            if is_serializable(expected_type):
                if isinstance(raw_value, expected_type):
                    data_parsed[k] = raw_value
                else:
                    data_parsed[k] = expected_type.from_serialized(raw_value)

            elif is_jsonvalue(raw_value):
                data_parsed[k] = raw_value

            else:
                raise TypeError(
                    f"Field {k!r} cannot be parsed as "
                    f"{expected_type!r}: {raw_value!r}"
                )

        return cast(ArgTypes, data_parsed)

    # conversions

    def serialize(self, **kwargs: Any) -> JSONValue:
        hints = get_type_hints(self._ArgTypes)
        data_serialized: dict[str, JSONValue] = {}

        for k, expected_type in hints.items():
            raw_value = self._data[k]

            if is_serializable(expected_type):
                data_serialized[k] = expected_type.serialize(raw_value)

            elif is_jsonvalue(raw_value):
                data_serialized[k] = raw_value

            else:
                raise TypeError(
                    f"Field {k!r} cannot be parsed as "
                    f"{JSONValue!s}: {raw_value!r}"
                    f"\n(this shouldn't be possible...)"
                )

        return data_serialized