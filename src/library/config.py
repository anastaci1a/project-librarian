# dep

from dataclasses import dataclass
from pathlib     import Path

from library.util import SomePath


# export

@dataclass(frozen=True)
class LibraryConfig:
    # attrs

    config_json:      SomePath = ".library/config.json"
    cached_json:      SomePath = ".library/cached.json"
    folder_meta_json: SomePath = ".folder/meta.json"

    # parse

    def __post_init__(self):
        for k in self.__dict__.keys():
            path = self.__getattribute__(k)
            self.__setattr__(k, Path(path))

    # method

    def to_dict(self) -> dict[str, str]:
        r = self.__dict__.copy()
        for k in r.keys():
            r[k] = str(r[k])
        return r
