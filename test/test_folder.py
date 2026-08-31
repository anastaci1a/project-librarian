import json

import pytest

from library import Library
from library.data import Meta


def test_data_delete_removes_folder_data_but_preserves_contents(tmp_path):
    library = Library(tmp_path)
    library.folders_create(Meta.create(name="Books"))
    folder = library.folders[0]
    content = folder.path_root / "book.txt"
    asset = folder.path_meta.parent / "icon.png"
    content.write_text("Keep me")
    asset.write_text("Delete me")

    folder.data_delete()

    assert not folder.path_meta.parent.exists()
    assert content.read_text() == "Keep me"
    assert folder not in library.folders
    assert json.loads(library.paths.cached_json.read_text()) == []


def test_folders_purge_deletes_data_for_every_folder(tmp_path):
    library = Library(tmp_path)
    library.folders_create(
        Meta.create(name="Books"),
        Meta.create(name="Music"),
    )
    folders = library.folders

    library.folders_purge()

    assert all(not folder.path_meta.parent.exists() for folder in folders)
    assert all(folder.path_root.exists() for folder in folders)
    assert library.folders == []
    assert json.loads(library.paths.cached_json.read_text()) == []


def test_deleted_folder_instance_is_inactive(tmp_path):
    library = Library(tmp_path)
    library.folders_create(Meta.create(name="Books"))
    folder = library.folders[0]

    folder.data_delete()

    with pytest.raises(RuntimeError, match="Folder instance is no longer active"):
        folder.meta_reset()
