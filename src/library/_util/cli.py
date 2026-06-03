# dep

from enum import Enum

from .parse import ArgParse


# const

BOX_CHARS_DEFAULT = "─│╭╮╰╯"


# cli formatting / displaying

class Ansi(Enum):
    F_RESET     = "\033[0m"
    F_BOLD      = "\033[1m"
    F_ITALIC    = "\033[3m"
    F_UNDERLINE = "\033[4m"

    def __str__(self):
        return self.value

class Cli:
    @staticmethod
    def print_boxed_text(
            text:  str,
            chars: str|None = BOX_CHARS_DEFAULT
    ) -> str|None:
        if chars is None:
            chars = BOX_CHARS_DEFAULT

        if len(chars) != 6: return None # err
        c_hori, c_vert, c_tl, c_tr, c_bl, c_br = chars

        lines = (
            text.strip()
            .replace("\t", " ")
            .replace("\r", "")
            .split("\n")
        )
        max_len = max([len(line) for line in lines])

        top_line = c_tl + (c_hori * (max_len + 2)) + c_tr
        bot_line = c_bl + (c_hori * (max_len + 2)) + c_br

        return "\n".join([
            top_line,
            *[f"{c_vert} {line.ljust(max_len)} {c_vert}" for line in lines],
            bot_line,
        ])

    @staticmethod
    def print_spacer() -> None:
        print("\n\n***\n")

    @staticmethod
    def print_title(
            title: str,
            title_chars: str,
            subtitle: str|None,
            prompt: str
    ) -> None:
        title = f"{Cli.print_boxed_text(title, title_chars)}\n\n"
        subtitle = f"{subtitle}\n\n" if subtitle not in (None, "") else ""

        input(
            f"{Ansi.F_BOLD}{title}{Ansi.F_RESET}"
            f"{Ansi.F_ITALIC}{subtitle}{Ansi.F_RESET}"
            f"{Ansi.F_BOLD}{prompt}{Ansi.F_RESET}"
        )

    @staticmethod
    def print_context(context: str|list[str]) -> None:
        context = ArgParse.str_list(context)
        print(f"{Ansi.F_ITALIC}{"\n".join(context)}{Ansi.F_RESET}")

    @staticmethod
    def print_directive(directive: str|list[str]) -> None:
        directive = ArgParse.str_list(directive)
        print(f"{Ansi.F_BOLD}{"\n".join(directive)}{Ansi.F_RESET}")

    @staticmethod
    def print_list(items: list[str]) -> None:
        i_just = len(f"{len(items)}")
        for i, item in enumerate(items):
            i_str = f"{i+1}.".ljust(i_just+1)
            print(f"{i_str} {item}")

    @staticmethod
    def prompt_list(items: list[str], prompt: str) -> int:
        Cli.print_directive(f"{prompt}\n")
        Cli.print_list(items)
        while True:
            user_input = input("> ")
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(items):
                    return idx
            except ValueError:
                pass