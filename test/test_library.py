# dep

from library      import Library
from library.data import Meta


# const

LIBRARY_ROOT = "./test/example-library-root"


# tests

def test_library_init() -> Library:
    input(f"press enter to load library at \"{LIBRARY_ROOT}\"...")
    lib = Library(LIBRARY_ROOT, load_cache=False)
    print("initialized.")
    try:
        lib.load_cache()
    except TypeError as e:
        print(f"(err: {e})")
    cached = len(lib.folders)
    print(f"loaded {cached} cached folders.\n")

    assert lib.paths.root.is_dir()
    assert lib.paths.config_json.is_file()

    return lib

def test_library_rescan(lib: Library):
    input("press enter to rescan...")
    start_amt = len(lib.folders); lib.rescan()
    print(f"found and loaded {len(lib.folders) - start_amt} new folders.\n")

def test_library_modif(lib: Library):
    folder_name = input(f"enter a folder to create... (enter to skip)\n> ")
    if folder_name == "": print("(skipped.)\n"); return
    new_folders = lib.folders_create(
        Meta.create(
            name=folder_name,
            tags={"Label": {"Cool Projects"}}
        ),
        refresh_meta=True
    )
    print(f"done. (library now contains {len(lib.folders)} folders.)\n")

    for f in new_folders:
        assert f.path_root.is_dir()
        assert f.path_meta.is_file()

def test_library_purge(lib: Library):
    user_input = input("press enter to purge... (type anything to skip)")
    if user_input != "": print("(skipped.)\n"); return
    lib.purge_all()
    print("done.\n")


# main

if __name__ == "__main__":
    print()
    lib = test_library_init()
    test_library_rescan(lib)
    test_library_modif(lib)
    test_library_purge(lib)