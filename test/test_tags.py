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


# main

if __name__ == "__main__":
    test_tags()