# dep

from library      import Library
from library.data import Meta


# tests

def test_library_loads():
    lib = Library("./test/example-library-root", load_cache=False)

    print("loading from cache...")
    try:
        lib.load_cache()
    except TypeError as e:
        print(f"(err: {e})")
    cached = len(lib.folders)
    print(f"loaded {cached} cached folders.\n")

    assert lib.paths.root.is_dir()
    assert lib.paths.config_json.is_file()

    input("press enter to rescan...")
    lib.rescan()
    print(f"found {len(lib.folders) - cached} new folders.\n")

    input("press enter to purge...")
    lib.purge_all()
    print("done.")
    exit()

def test_library_meta():
    lib = Library("./test/example-library-root")

    lib.folders_create(
        Meta.create(
            name="My Folder",
            tags={"Label": {"Cool Projects"}}
        ),
        refresh_meta=True
    )

    # expected first execution:
    # - generate [root]/My Folder/.folder/meta.json
    # - generate [root]/.library/cached.json

    # expected progressive executions:
    # - generate [root]/My Folder (1)/.folder/, /My Folder (2)/, /My Folder (3)/, ...

    print(len(lib.folders))

    # expected first execution:        1         (/Untitled/)
    # expected progressive executions: 2, 3, ... (/Untitled (2)/, /Untitled (3)/, ...)


# main

if __name__ == "__main__":
    test_library_loads()
    # test_library_meta()