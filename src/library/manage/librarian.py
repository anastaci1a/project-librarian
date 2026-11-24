# dep

from typing import Iterable

from ..data    import Tags, TagsInput
from ..library import Folder, Library


# librarian

class Librarian:
    # detection

    @classmethod
    def autodetect_tags(
            cls,
            to_process: Folder | Iterable[Folder] | Library,
            *,
            map_filetype: dict[str, Tags | TagsInput] = TagMap.FILETYPE_TO_TAGS
    ):
        pass