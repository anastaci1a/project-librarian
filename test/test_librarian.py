# dep

from library        import Library
from library.manage import Librarian

from test_library import *


# tests

def test_librarian(lib: Library):
    pass


# main

if __name__ == "__main__":
    lib = test_library_init()
    test_library_rescan(lib)
    test_librarian(lib)
