# dep

from random import randint
from typing import Iterable


# const

class Charset:
    ALPHANUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


# generators

class Generator:
    @classmethod
    def uid_generate(
            cls,
            digits: int = 16,
            *,
            exclude: Iterable[str] = (),
            charset: str = Charset.ALPHANUM,
            overflow_max: int = 50,
    ) -> str:
            def _generate(_count: int = 0):
                if _count >= overflow_max:
                    raise OverflowError("No remaining UIDs are available.")
                uid = cls._uid_generate(digits, charset=charset)
                if uid not in exclude: return uid
                return _generate(
                    _count=_count+1
                )
            return _generate()

    @classmethod
    def _uid_generate(
            cls,
            digits: int = 16,
            *,
            charset: str = Charset.ALPHANUM
    ) -> str:
        return "".join([
            charset[
                randint(0, len(charset)-1)
            ] for i in range(digits)
        ])