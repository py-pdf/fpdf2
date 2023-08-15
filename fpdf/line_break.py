"""
Routines for organizing lines and larger blocks of text, with manual and
automatic line wrapping.

The contents of this file are internal to fpdf, and not part of the public API.
They may change at any time without prior warning or any deprecation period.
"""

from typing import NamedTuple, Any, Optional, Union, Sequence

from .enums import CharVPos, WrapMode
from .errors import FPDFException
from .fonts import CoreFont, TTFFont
from .util import escape_parens

SOFT_HYPHEN = "\u00ad"
HYPHEN = "\u002d"
SPACE = " "
NEWLINE = "\n"


class Fragment:
    """
    A fragment of text with font/size/style and other associated information.
    """

    def __init__(
        self,
        characters: Union[list, str],
        graphics_state: dict,
        k: float,
        link: Optional[Union[int, str]] = None,
    ):
        if isinstance(characters, str):
            self.characters = list(characters)
        else:
            self.characters = characters
        self.graphics_state = graphics_state
        self.k = k
        self.link = link

    def __repr__(self):
        return (
            f"Fragment(characters={self.characters},"
            f" graphics_state={self.graphics_state},"
            f" k={self.k}, link={self.link})"
        )

    @property
    def font(self) -> Union[CoreFont, TTFFont]:
        return self.graphics_state["current_font"]

    @font.setter
    def font(self, v):
        self.graphics_state["current_font"] = v

    @property
    def is_ttf_font(self):
        return self.font and self.font.type == "TTF"

    @property
    def font_style(self):
        return self.graphics_state["font_style"]

    @property
    def font_family(self):
        return self.graphics_state["font_family"]

    @property
    def font_size_pt(self):
        size = self.graphics_state["font_size_pt"]
        vpos = self.graphics_state["char_vpos"]
        if vpos == CharVPos.SUB:
            size *= self.graphics_state["sub_scale"]
        elif vpos == CharVPos.SUP:
            size *= self.graphics_state["sup_scale"]
        elif vpos == CharVPos.NOM:
            size *= self.graphics_state["nom_scale"]
        elif vpos == CharVPos.DENOM:
            size *= self.graphics_state["denom_scale"]
        return size

    @property
    def font_size(self):
        return self.graphics_state["font_size_pt"] / self.k

    @property
    def font_stretching(self):
        return self.graphics_state["font_stretching"]

    @property
    def char_spacing(self):
        return self.graphics_state["char_spacing"]

    @property
    def text_mode(self):
        return self.graphics_state["text_mode"]

    @property
    def underline(self):
        return self.graphics_state["underline"]

    @property
    def draw_color(self):
        return self.graphics_state["draw_color"]

    @property
    def fill_color(self):
        return self.graphics_state["fill_color"]

    @property
    def text_color(self):
        return self.graphics_state["text_color"]

    @property
    def line_width(self):
        return self.graphics_state["line_width"]

    @property
    def char_vpos(self):
        return self.graphics_state["char_vpos"]

    @property
    def lift(self):
        vpos = self.graphics_state["char_vpos"]
        if vpos == CharVPos.SUB:
            lift = self.graphics_state["sub_lift"]
        elif vpos == CharVPos.SUP:
            lift = self.graphics_state["sup_lift"]
        elif vpos == CharVPos.NOM:
            lift = self.graphics_state["nom_lift"]
        elif vpos == CharVPos.DENOM:
            lift = self.graphics_state["denom_lift"]
        else:
            lift = 0.0
        return lift * self.graphics_state["font_size_pt"]

    @property
    def _text_shaping(self):
        return self.graphics_state["_text_shaping"]

    @property
    def string(self):
        return "".join(self.characters)

    def trim(self, index: int):
        self.characters = self.characters[:index]

    def __eq__(self, other: Any):
        return (
            self.characters == other.characters
            and self.graphics_state == other.graphics_state
            and self.k == other.k
        )

    def __hash__(self):
        return hash((self.characters, self.graphics_state, self.k))

    def get_width(
        self,
        start: int = 0,
        end: int = None,
        chars: str = None,
        initial_cs: bool = True,
    ):
        """
        Return the width of the string with the given font/size/style/etc.

        Args:
            start (int): Index of the start character. Default start of fragment.
            end (int): Index of the end character. Default end of fragment.
            chars (str): Specific text to get the width for (not necessarily the
                same as the contents of the fragment). If given, this takes
                precedence over the start/end arguments.
        """

        if chars is None:
            chars = self.characters[start:end]
        (char_len, w) = self.font.get_text_width(
            chars, self.font_size_pt, self._text_shaping
        )
        char_spacing = self.char_spacing
        if self.font_stretching != 100:
            w *= self.font_stretching * 0.01
            char_spacing *= self.font_stretching * 0.01
        if self.char_spacing != 0:
            # initial_cs must be False if the fragment is located at the
            # beginning of a text object, because the first char won't get spaced.
            if initial_cs:
                w += char_spacing * char_len
            else:
                w += char_spacing * (char_len - 1)
        return w / self.k

    def get_character_width(self, character: str, print_sh=False, initial_cs=True):
        """
        Return the width of a single character out of the stored text.
        """
        if character == SOFT_HYPHEN and not print_sh:
            # HYPHEN is inserted instead of SOFT_HYPHEN
            character = HYPHEN
        return self.get_width(chars=character, initial_cs=initial_cs)

    def render_pdf_text(self, frag_ws, current_ws, word_spacing, adjust_x, adjust_y, h):
        if self.is_ttf_font:
            if self._text_shaping:
                return self.render_with_text_shaping(
                    adjust_x, adjust_y, h, word_spacing, self._text_shaping
                )
            return self.render_pdf_text_ttf(frag_ws, word_spacing)
        return self.render_pdf_text_core(frag_ws, current_ws)

    def render_pdf_text_ttf(self, frag_ws, word_spacing):
        ret = ""
        mapped_text = ""
        for char in self.string:
            mapped_char = self.font.subset.pick(ord(char))
            if mapped_char:
                mapped_text += chr(mapped_char)
        if word_spacing:
            # do this once in advance
            u_space = escape_parens(" ".encode("utf-16-be").decode("latin-1"))

            # According to the PDF reference, word spacing shall be applied to every
            # occurrence of the single-byte character code 32 in a string when using
            # a simple font or a composite font that defines code 32 as a single-byte code.
            # It shall not apply to occurrences of the byte value 32 in multiple-byte codes.
            # FPDF uses 2 bytes per character (UTF-16-BE encoding) so the "Tw" operator doesn't work
            # As a workaround, we do word spacing using an adjustment before each space.
            # Determine the index of the space character (" ") in the current
            # subset and split words whenever this mapping code is found
            #
            words = mapped_text.split(chr(self.font.subset.pick(ord(" "))))
            words_strl = []
            for word_i, word in enumerate(words):
                # pylint: disable=redefined-loop-name
                word = escape_parens(word.encode("utf-16-be").decode("latin-1"))
                if word_i == 0:
                    words_strl.append(f"({word})")
                else:
                    adj = -(frag_ws * self.k) * 1000 / self.font_size_pt
                    words_strl.append(f"{adj:.3f}({u_space}{word})")
            escaped_text = " ".join(words_strl)
            ret += f"[{escaped_text}] TJ"
        else:
            escaped_text = escape_parens(
                mapped_text.encode("utf-16-be").decode("latin-1")
            )
            ret += f"({escaped_text}) Tj"
        return ret

    def render_with_text_shaping(
        self, pos_x, pos_y, h, word_spacing, text_shaping_parms
    ):
        ret = ""
        text = ""
        space_mapped_code = self.font.subset.pick(ord(" "))

        def adjust_pos(pos):
            return (
                pos
                * self.font.scale
                * self.font_size_pt
                * (self.font_stretching / 100)
                / 1000
                / self.k
            )

        char_spacing = self.char_spacing * (self.font_stretching / 100) / self.k
        for ti in self.font.shape_text(
            self.string, self.font_size_pt, text_shaping_parms
        ):
            if ti["mapped_char"] is None:  # Missing glyph
                continue
            char = chr(ti["mapped_char"]).encode("utf-16-be").decode("latin-1")
            if ti["x_offset"] != 0 or ti["y_offset"] != 0:
                if text:
                    ret += f"({text}) Tj "
                    text = ""
                offsetx = pos_x + adjust_pos(ti["x_offset"])
                offsety = pos_y - adjust_pos(ti["y_offset"])
                ret += (
                    f"1 0 0 1 {(offsetx) * self.k:.2f} {(h - offsety) * self.k:.2f} Tm "
                )
            text += char
            pos_x += adjust_pos(ti["x_advance"]) + char_spacing
            pos_y += adjust_pos(ti["y_advance"])
            if word_spacing and ti["mapped_char"] == space_mapped_code:
                pos_x += word_spacing

            # if only moving "x" we don't need to move the text matrix
            if ti["force_positioning"] or (
                word_spacing and ti["mapped_char"] == space_mapped_code
            ):
                if text:
                    ret += f"({text}) Tj "
                    text = ""
                ret += f"1 0 0 1 {(pos_x) * self.k:.2f} {(h - pos_y) * self.k:.2f} Tm "

        if text:
            ret += f"({text}) Tj"
        return ret

    def render_pdf_text_core(self, frag_ws, current_ws):
        ret = ""
        if frag_ws != current_ws:
            ret += f"{frag_ws * self.k:.3f} Tw "
        escaped_text = escape_parens(self.string)
        ret += f"({escaped_text}) Tj"
        return ret


class TextLine(NamedTuple):
    fragments: tuple
    text_width: float
    number_of_spaces: int
    justify: bool
    trailing_nl: bool = False


class SpaceHint(NamedTuple):
    original_fragment_index: int
    original_character_index: int
    current_line_fragment_index: int
    current_line_character_index: int
    line_width: float
    number_of_spaces: int


class HyphenHint(NamedTuple):
    original_fragment_index: int
    original_character_index: int
    current_line_fragment_index: int
    current_line_character_index: int
    line_width: float
    number_of_spaces: int
    curchar: str
    curchar_width: float
    graphics_state: dict
    k: float


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
        graphics_state: dict,
        k: float,
        original_fragment_index: int,
        original_character_index: int,
        url: str = None,
    ):
        assert character != NEWLINE
        if not self.fragments:
            self.fragments.append(Fragment("", graphics_state, k, url))

        # characters are expected to be grouped into fragments by font and
        # character attributes. If the last existing fragment doesn't match
        # the properties of the pending character -> add a new fragment.
        elif (
            graphics_state != self.fragments[-1].graphics_state
            or k != self.fragments[-1].k
        ):
            self.fragments.append(Fragment("", graphics_state, k, url))
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
                graphics_state,
                k,
            )

        if character != SOFT_HYPHEN or self.print_sh:
            self.width += character_width
            active_fragment.characters.append(character)

    def trim_trailing_spaces(self):
        if not self.fragments:
            return
        last_frag = self.fragments[-1]
        last_char = last_frag.characters[-1]
        while last_char == " ":
            char_width = last_frag.get_character_width(" ")
            self.width -= char_width
            last_frag.trim(-1)
            if not last_frag.characters:
                del self.fragments[-1]
            if not self.fragments:
                return
            last_frag = self.fragments[-1]
            last_char = last_frag.characters[-1]

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
        self.width = break_hint.line_width

    def manual_break(self, justify: bool = False, trailing_nl: bool = False):
        return TextLine(
            fragments=self.fragments,
            text_width=self.width,
            number_of_spaces=self.number_of_spaces,
            justify=(self.number_of_spaces > 0) and justify,
            trailing_nl=trailing_nl,
        )

    def automatic_break_possible(self):
        return self.hyphen_break_hint is not None or self.space_break_hint is not None

    def automatic_break(self, justify: bool):
        assert self.automatic_break_possible()
        if self.hyphen_break_hint is not None and (
            self.space_break_hint is None
            or self.hyphen_break_hint.line_width > self.space_break_hint.line_width
        ):
            self._apply_automatic_hint(self.hyphen_break_hint)
            self.add_character(
                self.hyphen_break_hint.curchar,
                self.hyphen_break_hint.curchar_width,
                self.hyphen_break_hint.graphics_state,
                self.hyphen_break_hint.k,
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
        justify: bool = False,
        print_sh: bool = False,
        wrapmode: WrapMode = WrapMode.WORD,
    ):
        self.styled_text_fragments = styled_text_fragments
        self.justify = justify
        self.print_sh = print_sh
        self.wrapmode = wrapmode
        self.fragment_index = 0
        self.character_index = 0
        self.idx_last_forced_break = None

    # pylint: disable=too-many-return-statements
    def get_line_of_given_width(self, maximum_width: float):
        first_char = True  # "Tw" ignores the first character in a text object.
        idx_last_forced_break = self.idx_last_forced_break
        self.idx_last_forced_break = None

        if self.fragment_index == len(self.styled_text_fragments):
            return None

        current_line = CurrentLine(print_sh=self.print_sh)
        while self.fragment_index < len(self.styled_text_fragments):
            current_fragment = self.styled_text_fragments[self.fragment_index]

            if self.character_index >= len(current_fragment.characters):
                self.character_index = 0
                self.fragment_index += 1
                continue

            character = current_fragment.characters[self.character_index]
            character_width = current_fragment.get_character_width(
                character, self.print_sh, initial_cs=not first_char
            )
            first_char = False

            if character == NEWLINE:
                self.character_index += 1
                return current_line.manual_break(trailing_nl=True)

            if current_line.width + character_width > maximum_width:
                if character == SPACE:  # must come first, always drop a current space.
                    self.character_index += 1
                    return current_line.manual_break(self.justify)
                if self.wrapmode == WrapMode.CHAR:
                    # If the line ends with one or more spaces, then we want to get rid of them
                    # so it can be justified correctly.
                    current_line.trim_trailing_spaces()
                    return current_line.manual_break(self.justify)
                if current_line.automatic_break_possible():
                    (
                        self.fragment_index,
                        self.character_index,
                        line,
                    ) = current_line.automatic_break(self.justify)
                    self.character_index += 1
                    return line
                if idx_last_forced_break == self.character_index:
                    raise FPDFException(
                        "Not enough horizontal space to render a single character"
                    )
                self.idx_last_forced_break = self.character_index
                return current_line.manual_break()

            current_line.add_character(
                character,
                character_width,
                current_fragment.graphics_state,
                current_fragment.k,
                self.fragment_index,
                self.character_index,
                current_fragment.link,
            )

            self.character_index += 1

        if current_line.width:
            return current_line.manual_break()
        return None
