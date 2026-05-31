# dep

from library import *


# tests

def test_tags():
    print("TAG TEST")

    combined_immut = TagUtil.combine(
            {"Category": {"Package"}, "Language": {"Java"}},
            {"Category": {"Mobile"}, "Language": {"Kotlin"}},
            {"Category": {"Web"}, "Language": {"HTML", "Typescript"}}
    )
    print("1:", TagUtil.serialize(combined_immut))
    # expected: {"Category": {"Mobile", "Package", "Web"}, "Language": {"HTML", "Java", "Kotlin", "Typescript"}}

def test_meta():
    print("META TEST")

    meta = Meta(tags={"Status": {"Inactive"}})
    print("1:", meta)
    # expected: Meta(name="Untitled", ..., tags: Mapping[str, frozenset[str]], ...)

    meta_dict = meta.to_dict()
    print("2:", meta_dict)
    # expected: {"name": "Untitled", ..., "tags": dict[str, list[str]], ...}

    testfile = "./test.temp.json"
    JSONFile.write(testfile, meta_dict)
    meta_dict_fromfile = JSONFile.read(testfile)
    print("3:", meta_dict_fromfile)
    # expected: {"name": "Untitled", ..., "tags": dict[str, list[str]], ...}

    meta_fromfile = meta.from_dict(meta_dict_fromfile)
    print("4:", meta_fromfile)
    # expected: Meta(name="Untitled", ..., tags: Mapping[str, frozenset[str]], ...)

    print("5:", meta == meta_fromfile)
    # expected: True


# main

if __name__ == "__main__":
    test_tags(); print()
    test_meta()