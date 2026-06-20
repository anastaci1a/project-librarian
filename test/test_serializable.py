# dep

from __future__ import annotations

from library._util.data import Meta # only for testing


# test

def test_serializable():
    meta = Meta.create(
        name="Test"
    )

    print(meta.data) # expected: dict[str, JSONValue | Serializable]


# main

if __name__ == "__main__":
    test_serializable()