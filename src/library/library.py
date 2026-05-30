# dep

from __future__  import annotations
from dataclasses import dataclass
from functools import cached_property

from .data import Meta, Tags


# export

@dataclass
class Book:
    meta: Meta

class Library:
    # constr

    def __init__(self):
        self._books: list[Book] = []

    # get

    @property
    def books(self) -> list[Book]:
        return self._books.copy()

    @cached_property
    def tags(self) -> Tags:
        pass

    def add_books(self, *books: Book):
        self.__dict__.pop("tags", None)