from typing import NamedTuple, Any, Union, Sequence

from .errors import FPDFException

SOFT_HYPHEN = "\u00ad"
HYPHEN = "\u002d"
SPACE = " "
NEWLINE = "\n"


class Fragment:
    def __init__(self, style: str, underlined: bool, characters: str = None):
        self.style = style
        self.underline = underlined
        self.characters = [] if characters is None else characters

    def __repr__(self):
        return f"Fragment(style={self.style}, underline={self.underline}, characters={self.characters})"

    @classmethod
    def from_string(cls, string: str, style: str, underlined: bool):
        return cls(style, underlined, list(string))

    def trim(self, index: int):
        self.characters = self.characters[:index]

    @property
    def string(self):
        return "".join(self.characters)

    def __eq__(self, other: Any):
        return (
            self.characters == other.characters
            and self.style == other.style
            and self.underline == other.underline
        )


class TextLine(NamedTuple):
    fragments: tuple
    text_width: float
    number_of_spaces_between_words: int
    justify: bool
    trailing_nl: bool


class SpaceHint(NamedTuple):
    original_fragment_index: int
    original_character_index: int
    current_line_fragment_index: int
    current_line_character_index: int
    width: float
    number_of_spaces: int


class HyphenHint(NamedTuple):
    original_fragment_index: int
    original_character_index: int
    current_line_fragment_index: int
    current_line_character_index: int
    width: float
    number_of_spaces: int
    character_to_append: str
    character_to_append_width: float
    character_to_append_style: str
    character_to_append_underline: bool


class CurrentLine:
    def __init__(self, print_sh: bool = False):
        """
        Per-line text fragment management for use by MultiLineBreak.
            Args:
                print_sh (bool): If true, a soft-hyphen will be rendered
                    normally, instead of triggering a line break. Default: False
        """
        self.print_sh = print_sh
        self.fragments = []
        self.width = 0
        self.number_of_spaces = 0

        # automatic break hints
        # CurrentLine class remembers 3 positions
        # 1 - position of last inserted character.
        #     class attributes (`width`, `fragments`)
        #     is used for this purpose
        # 2 - position of last inserted space
        #     SpaceHint is used fo this purpose.
        # 3 - position of last inserted soft-hyphen
        #     HyphenHint is used fo this purpose.
        # The purpose of multiple positions tracking - to have an ability
        # to break in multiple places, depending on condition.
        self.space_break_hint = None
        self.hyphen_break_hint = None

    def add_character(
        self,
        character: str,
        character_width: float,
        style: str,
        underline: bool,
        original_fragment_index: int,
        original_character_index: int,
    ):
        assert character != NEWLINE

        if not self.fragments:
            self.fragments.append(Fragment(style, underline))

        # characters are expected to be grouped into fragments by styles and
        # underline attributes. If the last existing fragment doesn't match
        # the (style, underline) of pending character ->
        # create a new fragment with matching (style, underline)
        elif (
            style != self.fragments[-1].style
            or underline != self.fragments[-1].underline
        ):
            self.fragments.append(Fragment(style, underline))
        active_fragment = self.fragments[-1]

        if character == SPACE:
            self.space_break_hint = SpaceHint(
                original_fragment_index,
                original_character_index,
                len(self.fragments),
                len(active_fragment.characters),
                self.width,
                self.number_of_spaces,
            )
            self.number_of_spaces += 1
        elif character == SOFT_HYPHEN and not self.print_sh:
            self.hyphen_break_hint = HyphenHint(
                original_fragment_index,
                original_character_index,
                len(self.fragments),
                len(active_fragment.characters),
                self.width,
                self.number_of_spaces,
                HYPHEN,
                character_width,
                style,
                underline,
            )

        if character != SOFT_HYPHEN or self.print_sh:
            self.width += character_width
            active_fragment.characters.append(character)

    def _apply_automatic_hint(self, break_hint: Union[SpaceHint, HyphenHint]):
        """
        This function mutates the current_line, applying one of the states
        observed in the past and stored in
        `hyphen_break_hint` or `space_break_hint` attributes.
        """
        self.fragments = self.fragments[: break_hint.current_line_fragment_index]
        if self.fragments:
            self.fragments[-1].trim(break_hint.current_line_character_index)
        self.number_of_spaces = break_hint.number_of_spaces
        self.width = break_hint.width

    def manual_break(self, justify: bool = False, trailing_nl: bool = False):
        return TextLine(
            fragments=self.fragments,
            text_width=self.width,
            number_of_spaces_between_words=self.number_of_spaces,
            justify=(self.number_of_spaces > 0) and justify,
            trailing_nl=trailing_nl,
        )

    def automatic_break_possible(self):
        return self.hyphen_break_hint is not None or self.space_break_hint is not None

    def automatic_break(self, justify: bool):
        assert self.automatic_break_possible()
        if self.hyphen_break_hint is not None and (
            self.space_break_hint is None
            or self.hyphen_break_hint.width > self.space_break_hint.width
        ):
            self._apply_automatic_hint(self.hyphen_break_hint)
            self.add_character(
                self.hyphen_break_hint.character_to_append,
                self.hyphen_break_hint.character_to_append_width,
                self.hyphen_break_hint.character_to_append_style,
                self.hyphen_break_hint.character_to_append_underline,
                self.hyphen_break_hint.original_fragment_index,
                self.hyphen_break_hint.original_character_index,
            )
            return (
                self.hyphen_break_hint.original_fragment_index,
                self.hyphen_break_hint.original_character_index,
                self.manual_break(justify),
            )
        self._apply_automatic_hint(self.space_break_hint)
        return (
            self.space_break_hint.original_fragment_index,
            self.space_break_hint.original_character_index,
            self.manual_break(justify),
        )


class MultiLineBreak:
    def __init__(
        self,
        styled_text_fragments: Sequence,
        size_by_style: Sequence,
        justify: bool = False,
        print_sh: bool = False,
    ):
        self.styled_text_fragments = styled_text_fragments
        self.size_by_style = size_by_style
        self.justify = justify
        self.print_sh = print_sh
        self.fragment_index = 0
        self.character_index = 0
        self.char_index_for_last_forced_manual_break = None

    def _get_character_width(self, character: str, style: str = ""):
        if character == SOFT_HYPHEN and not self.print_sh:
            # HYPHEN is inserted instead of SOFT_HYPHEN
            character = HYPHEN
        return self.size_by_style(character, style)

    # pylint: disable=too-many-return-statements
    def get_line_of_given_width(self, maximum_width: float, wordsplit: bool = True):
        char_index_for_last_forced_manual_break = (
            self.char_index_for_last_forced_manual_break
        )
        self.char_index_for_last_forced_manual_break = None

        if self.fragment_index == len(self.styled_text_fragments):
            return None

        last_fragment_index = self.fragment_index
        last_character_index = self.character_index
        line_full = False

        current_line = CurrentLine(print_sh=self.print_sh)
        while self.fragment_index < len(self.styled_text_fragments):

            current_fragment = self.styled_text_fragments[self.fragment_index]

            if self.character_index >= len(current_fragment.characters):
                self.character_index = 0
                self.fragment_index += 1
                continue

            character = current_fragment.characters[self.character_index]
            character_width = self._get_character_width(
                character, current_fragment.style
            )

            if character == NEWLINE:
                self.character_index += 1
                return current_line.manual_break(trailing_nl=True)

            if current_line.width + character_width > maximum_width:
                if character == SPACE:
                    self.character_index += 1
                    return current_line.manual_break(self.justify)
                if current_line.automatic_break_possible():
                    (
                        self.fragment_index,
                        self.character_index,
                        line,
                    ) = current_line.automatic_break(self.justify)
                    self.character_index += 1
                    return line
                if not wordsplit:
                    line_full = True
                    break
                if char_index_for_last_forced_manual_break == self.character_index:
                    raise FPDFException(
                        "Not enough horizontal space to render a single character"
                    )
                self.char_index_for_last_forced_manual_break = self.character_index
                return current_line.manual_break()

            current_line.add_character(
                character,
                character_width,
                current_fragment.style,
                current_fragment.underline,
                self.fragment_index,
                self.character_index,
            )

            self.character_index += 1

        if line_full and not wordsplit:
            # roll back and return empty line to trigger continuation
            # on the next line.
            self.fragment_index = last_fragment_index
            self.character_index = last_character_index
            return CurrentLine().manual_break(self.justify)
        if current_line.width:
            return current_line.manual_break()
