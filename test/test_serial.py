# dep

from library.data import Meta


# test

def test_serializable():
    meta = Meta.create(
        name="Test"
    )

    assert meta.name == "Test"


# main

if __name__ == "__main__":
    test_serializable()
