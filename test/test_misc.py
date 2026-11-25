# dep

from library.data.meta import Meta


# test

def test_misc():
    meta = Meta(
        name="test",
        tags={}
    )
    print(meta)


# main

if __name__ == "__main__":
    test_misc()
