# dep

from library import Meta


# test

def test_serializable():
    meta = Meta.create(
        name="Test"
    )

    print(meta.data) # expected: dict[str, JSONValue | Serializable]


# main

if __name__ == "__main__":
    test_serializable()