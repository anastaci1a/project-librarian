# dep

from library._util.data import Meta # only for testing

from library import *


# tests

def test_library():
    lib = Library("./test/example-library-root")

    # expected:
    # - generate [root]/.library/config.json
    # - (nothing else)

    lib.folders_create(
        Meta.create(),
        refresh_meta=True,
        rename_folder_collisions=True
    )

    # expected first execution:
    # - generate [root]/Untitled/.folder/meta.json
    #   - (has date_created and date_modified)
    # - generate [root]/.library/cached.json

    # expected progressive executions:
    # - generate [root]/Untitled (1)/.folder/, /Untitled (2)/, /Untitled (3)/, ...

    print(len(lib.folders))

    # expected first execution:        1         (/Untitled/)
    # expected progressive executions: 2, 3, ... (/Untitled (2)/, /Untitled (3)/, ...)


# main

if __name__ == "__main__":
    test_library()