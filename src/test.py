# dep

from library.data import tags_combine


# tests

def test_tags():
    # expected:
    # {"Category": {"Web", "Mobile", "Package"}, "Language": {"Typescript", "HTML", "Kotlin", "Java"}}

    print(tags_combine(
        {"Category": {"Package"}, "Language": {"Java"}},
        {"Category": {"Mobile"}, "Language": {"Kotlin"}},
        {"Category": {"Web"}, "Language": {"HTML", "Typescript"}}
    ))


# main

if __name__ == "__main__":
    test_tags()