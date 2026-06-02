# dep

from library import *


# tests

def test_library():
    lib = Library(
        "./test/example-library-root",
        update_folder_meta=True
    )
    # expected:
    # - generate [root]/.library/config.json
    # - generate [root]/*/.folder/meta.json (in each existing folder)
    #   - (each has date_created and date_modified)

    lib.add_folders(
        Folder(Meta(
            name="_NEW_"
        )),
        update_meta=True
    )
    # expected:
    # - generate [root]/_NEW_/.folder/meta.json
    #   - (has date_created and date_modified)

    # print(len(lib.folders))
    # expected: number of folders in [root], excluding .library

# main

if __name__ == "__main__":
    test_library()