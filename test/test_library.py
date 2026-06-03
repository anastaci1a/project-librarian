# dep

from pathlib import Path

from library import *


# tests

def test_library():
    lib = Library("./test/example-library-root")
    # expected:
    # - generate [root]/.library/config.json
    # - generate [root]/*/.folder/meta.json (in each existing folder)
    #   - (each has date_created and date_modified)

    Folder.create(lib, meta=Meta(name="_NEW_"), refresh_meta=True)
    # expected:
    # - generate [root]/_NEW_/.folder/meta.json
    #   - (has date_created and date_modified)
    # for each progressive execution:
    # - generate [root]/_NEW_ (1)/.folder/, /_NEW_ (2)/, /_NEW_ (3)/, ...

    # print(len(lib.folders))
    # expected: number of folders in [root], excluding .library

# main

if __name__ == "__main__":
    test_library()