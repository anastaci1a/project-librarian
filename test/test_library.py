# dep

from library import *


# tests

def test_library():
    lib = Library("./test/example-library-root")

    # expected:
    # - generate [root]/.library/config.json
    # - (nothing else)

    lib.folders_create(
        Meta(),
        refresh_meta=True,
        rename_folder_collisions=True
    )

    # expected first execution:
    # - generate [root]/Untitled/.folder/meta.json
    #   - (has date_created and date_modified)
    # - generate [root]/.library/cached.json

    # expected progressive executions:
    # - generate [root]/Untitled/.folder/, /Untitled (2)/, ...

    print(len(lib.folders))

    # expected first execution:        0         (none)
    # expected progressive executions: 1, 2, ... (/Untitled/, /Untitled (2)/, ...)

# main

if __name__ == "__main__":
    test_library()