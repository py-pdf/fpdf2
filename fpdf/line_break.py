"""
Routines for organizing lines and larger blocks of text, with manual and
automatic line wrapping.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/LineBreaks.html>
"""

from numbers import Number
from typing import NamedTuple, Any, List, Optional, Union, Sequence
from uuid import uuid4

from .enums import Align, CharVPos, TextDirection, WrapMode
from .errors import FPDFException
from .fonts import CoreFont, TTFFont
from .util import escape_parens

SOFT_HYPHEN = "\u00ad"
HYPHEN = "\u002d"
SPACE = " "
BREAKING_SPACE_SYMBOLS = [
    " ",
    "\u200b",  # | ZERO WIDTH SPACE
    "\u2000",  # | EN QUAD
    "\u2001",  # | EM QUAD
    "\u2002",  # | EN SPACE
    "\u2003",  # | EM SPACE
    "\u2004",  # | THREE-PER-EM SPACE
    "\u2005",  # | FOUR-PER-EM SPACE
    "\u2006",  # | SIX-PER-EM SPACE
    "\u2008",  # | PUNCTUATION SPACE
    "\u2009",  # | THIN SPACE
    "\u200a",  # | HAIR SPACE
    "\u205f",  # | MEDIUM MATHEMATICAL SPACE
    "\u3000",  # | IDEOGRAPHIC SPACE
    "\u0009",  # | TAB
]
BREAKING_SPACE_SYMBOLS_STR = "".join(BREAKING_SPACE_SYMBOLS)
NBSP = "\u00a0"
NEWLINE = "\n"
FORM_FEED = "\u000c"


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
    def strikethrough(self):
        return self.graphics_state["strikethrough"]

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
    def string(self):
        return "".join(self.characters)

    @property
    def width(self):
        return self.get_width()

    @property
    def text_shaping_parameters(self):
        return self.graphics_state["text_shaping"]

    @property
    def paragraph_direction(self):
        return (
            self.text_shaping_parameters["paragraph_direction"]
            if self.text_shaping_parameters
            else TextDirection.LTR
        )

    @property
    def fragment_direction(self):
        return (
            self.text_shaping_parameters["fragment_direction"]
            if self.text_shaping_parameters
            else TextDirection.LTR
        )

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
            chars, self.font_size_pt, self.text_shaping_parameters
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

    def has_same_style(self, other: "Fragment"):
        """Returns if 2 fragments are equivalent other than the characters/string"""
        return (
            self.graphics_state == other.graphics_state
            and self.k == other.k
            and self.__class__ == other.__class__
        )

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
            if self.text_shaping_parameters:
                return self.render_with_text_shaping(
                    adjust_x, adjust_y, h, word_spacing
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
            u_space = self.font.escape_text(" ")

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
                word = self.font.escape_text(word)
                if word_i == 0:
                    words_strl.append(f"({word})")
                else:
                    adj = -(frag_ws * self.k) * 1000 / self.font_size_pt
                    words_strl.append(f"{adj:.3f}({u_space}{word})")
            escaped_text = " ".join(words_strl)
            ret += f"[{escaped_text}] TJ"
        else:
            escaped_text = self.font.escape_text(mapped_text)
            ret += f"({escaped_text}) Tj"
        return ret

    def render_with_text_shaping(self, pos_x, pos_y, h, word_spacing):
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
            self.string, self.font_size_pt, self.text_shaping_parameters
        ):
            if ti["mapped_char"] is None:  # Missing glyph
                continue
            char = self.font.escape_text(chr(ti["mapped_char"]))
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


class TotalPagesSubstitutionFragment(Fragment):
    """
    A special type of text fragment that represents a placeholder for the total number of pages
    in a PDF document.

    A placeholder will be generated during the initial content rendering phase of a PDF document.
    This placeholder is later replaced by the total number of pages in the document when the final
    output is being produced.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = uuid4()

    def get_placeholder_string(self):
        """
        This method returns a placeholder string containing a universally unique identifier (UUID4),
        ensuring that the placeholder is distinct and does not conflict with other placeholders
        within the document.
        """
        return f"::placeholder:{self.uuid}::"

    def render_pdf_text(self, *args, **kwargs):
        """
        This method is invoked during the page content rendering phase, which is common to all
        `Fragment` instances. It stores the provided arguments and keyword arguments to preserve
        the necessary information and graphic state for the final substitution rendering.

        The method then returns the unique placeholder string.
        """
        self._render_args = args
        self._render_kwargs = kwargs
        return self.get_placeholder_string()

    def render_text_substitution(self, replacement_text: str):
        """
        This method is invoked at the output phase. It calls `render_pdf_text()` from the superclass
        to render the fragment with the preserved rendering state (stored in `_render_args` and `_render_kwargs`)
        and insert the final text in place of the placeholder.
        """
        self.characters = list(replacement_text)
        return super().render_pdf_text(*self._render_args, **self._render_kwargs)


class TextLine(NamedTuple):
    fragments: tuple
    text_width: float
    number_of_spaces: int
    align: Align
    height: float
    max_width: float
    trailing_nl: bool = False
    trailing_form_feed: bool = False
    indent: float = 0

    def get_ordered_fragments(self):
        if not self.fragments:
            return tuple()
        directional_runs = []
        direction = None
        for fragment in self.fragments:
            if direction is not None and fragment.fragment_direction == direction:
                directional_runs[-1].append(fragment)
            else:
                directional_runs.append([fragment])
                direction = fragment.fragment_direction
        if self.fragments[0].paragraph_direction == TextDirection.RTL or (
            not self.fragments[0].paragraph_direction
            and self.fragments[0].fragment_direction == TextDirection.RTL
        ):
            directional_runs = directional_runs[::-1]
        ordered_fragments = []
        for run in directional_runs:
            ordered_fragments += (
                run[::-1] if run[0].fragment_direction == TextDirection.RTL else run
            )
        return tuple(ordered_fragments)


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
    def __init__(self, max_width: float, print_sh: bool = False, indent: float = 0):
        """
        Per-line text fragment management for use by MultiLineBreak.
            Args:
                print_sh (bool): If true, a soft-hyphen will be rendered
                    normally, instead of triggering a line break. Default: False
        """
        self.max_width = max_width
        self.print_sh = print_sh
        self.indent = indent
        self.fragments: List[Fragment] = []
        self.height = 0
        self.number_of_spaces = 0

        # automatic break hints
        # CurrentLine class remembers 3 positions
        # 1 - position of last inserted character.
        #     class attributes (`width`, `fragments`)
        #     is used for this purpose
        # 2 - position of last inserted space
        #     SpaceHint is used for this purpose.
        # 3 - position of last inserted soft-hyphen
        #     HyphenHint is used for this purpose.
        # The purpose of multiple positions tracking - to have an ability
        # to break in multiple places, depending on condition.
        self.space_break_hint = None
        self.hyphen_break_hint = None

    @property
    def width(self):
        width = 0
        for i, fragment in enumerate(self.fragments):
            width += fragment.get_width(initial_cs=i > 0)
        return width

    def add_character(
        self,
        character: str,
        character_width: float,
        original_fragment: Fragment,
        original_fragment_index: int,
        original_character_index: int,
        height: float,
        url: str = None,
    ):
        assert character != NEWLINE
        self.height = height
        if not self.fragments:
            self.fragments.append(
                original_fragment.__class__(
                    characters="",
                    graphics_state=original_fragment.graphics_state,
                    k=original_fragment.k,
                    link=url,
                )
            )

        # characters are expected to be grouped into fragments by font and
        # character attributes. If the last existing fragment doesn't match
        # the properties of the pending character -> add a new fragment.
        elif isinstance(
            original_fragment, Fragment
        ) and not original_fragment.has_same_style(self.fragments[-1]):
            self.fragments.append(
                original_fragment.__class__(
                    characters="",
                    graphics_state=original_fragment.graphics_state,
                    k=original_fragment.k,
                    link=url,
                )
            )
        active_fragment = self.fragments[-1]

        if character in BREAKING_SPACE_SYMBOLS_STR:
            self.space_break_hint = SpaceHint(
                original_fragment_index,
                original_character_index,
                len(self.fragments),
                len(active_fragment.characters),
                self.width,
                self.number_of_spaces,
            )
            self.number_of_spaces += 1
        elif character == NBSP:
            # PDF viewers ignore NBSP for word spacing with "Tw".
            character = SPACE
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
                original_fragment.graphics_state,
                original_fragment.k,
            )

        if character != SOFT_HYPHEN or self.print_sh:
            active_fragment.characters.append(character)

    def trim_trailing_spaces(self):
        if not self.fragments:
            return
        last_frag = self.fragments[-1]
        last_char = last_frag.characters[-1]
        while last_char == " ":
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

    def manual_break(
        self, align: Align, trailing_nl: bool = False, trailing_form_feed: bool = False
    ):
        return TextLine(
            fragments=self.fragments,
            text_width=self.width,
            number_of_spaces=self.number_of_spaces,
            align=align,
            height=self.height,
            max_width=self.max_width - self.indent,
            trailing_nl=trailing_nl,
            trailing_form_feed=trailing_form_feed,
            indent=self.indent,
        )

    def automatic_break_possible(self):
        return self.hyphen_break_hint is not None or self.space_break_hint is not None

    def automatic_break(self, align: Align):
        assert self.automatic_break_possible()
        if self.hyphen_break_hint is not None and (
            self.space_break_hint is None
            or self.hyphen_break_hint.line_width > self.space_break_hint.line_width
        ):
            self._apply_automatic_hint(self.hyphen_break_hint)
            self.add_character(
                self.hyphen_break_hint.curchar,
                self.hyphen_break_hint.curchar_width,
                self.hyphen_break_hint,
                self.hyphen_break_hint.original_fragment_index,
                self.hyphen_break_hint.original_character_index,
                self.height,
            )
            return (
                self.hyphen_break_hint.original_fragment_index,
                self.hyphen_break_hint.original_character_index,
                self.manual_break(align),
            )
        self._apply_automatic_hint(self.space_break_hint)
        return (
            self.space_break_hint.original_fragment_index,
            self.space_break_hint.original_character_index,
            self.manual_break(align),
        )


class MultiLineBreak:
    def __init__(
        self,
        fragments: Sequence[Fragment],
        max_width: Union[float, callable],
        margins: Sequence[Number],
        align: Align = Align.L,
        print_sh: bool = False,
        wrapmode: WrapMode = WrapMode.WORD,
        line_height: float = 1.0,
        skip_leading_spaces: bool = False,
        first_line_indent: float = 0,
    ):
        """Accept text as Fragments, to be split into individual lines depending
        on line width and text height.
        Args:
            fragments: A sequence of Fragment()s containing text.
            max_width: Either a fixed width as float or a callback function
                get_width(height). If a function, it gets called with the largest
                height encountered on the current line, and must return the
                applicable width for the line with the given height at the current
                vertical position. The height is relevant in those cases where the
                lateral boundaries of the enclosing TextRegion() are not vertical.
            margins (sequence of floats): The extra clearance that may apply at the beginning
                and/or end of a line (usually either FPDF.c_margin or 0.0 for each side).
            align (Align): The horizontal alignment of the current text block.
            print_sh (bool): If True, a soft-hyphen will be rendered
                normally, instead of triggering a line break. Default: False
            wrapmode (WrapMode): Selects word or character based wrapping.
            line_height (float, optional): A multiplier relative to the font
                size changing the vertical space occupied by a line of text. Default 1.0.
            skip_leading_spaces (bool, optional): On each line, any space characters
                at the beginning will be skipped. Default value: False.
            first_line_indent (float, optional): left spacing before first line of text in paragraph.
        """

        self.fragments = fragments
        if callable(max_width):
            self.get_width = max_width
        else:
            self.get_width = lambda height: max_width
        self.margins = margins
        self.align = align
        self.print_sh = print_sh
        self.wrapmode = wrapmode
        self.line_height = line_height
        self.skip_leading_spaces = skip_leading_spaces
        self.fragment_index = 0
        self.character_index = 0
        self.idx_last_forced_break = None
        self.first_line_indent = first_line_indent
        self._is_first_line = True

    # pylint: disable=too-many-return-statements
    def get_line(self):
        first_char = True  # "Tw" ignores the first character in a text object.
        idx_last_forced_break = self.idx_last_forced_break
        self.idx_last_forced_break = None

        if self.fragment_index == len(self.fragments):
            return None

        current_font_height = 0

        max_width = self.get_width(current_font_height)
        # The full max width will be passed on via TextLine to FPDF._render_styled_text_line().
        current_line = CurrentLine(
            max_width=max_width,
            print_sh=self.print_sh,
            indent=self.first_line_indent if self._is_first_line else 0,
        )
        # For line wrapping we need to use the reduced width.
        for margin in self.margins:
            max_width -= margin
        if self._is_first_line:
            max_width -= self.first_line_indent

        if self.skip_leading_spaces:
            # write_html() with TextColumns uses this, since it can't know in
            # advance where the lines will be broken.
            while self.fragment_index < len(self.fragments):
                if self.character_index >= len(
                    self.fragments[self.fragment_index].characters
                ):
                    self.character_index = 0
                    self.fragment_index += 1
                    continue
                character = self.fragments[self.fragment_index].characters[
                    self.character_index
                ]
                if character == SPACE:
                    self.character_index += 1
                else:
                    break

        while self.fragment_index < len(self.fragments):
            current_fragment = self.fragments[self.fragment_index]

            if current_fragment.font_size > current_font_height:
                current_font_height = current_fragment.font_size  # document units
                max_width = self.get_width(current_font_height)
                current_line.max_width = max_width
                for margin in self.margins:
                    max_width -= margin
                if self._is_first_line:
                    max_width -= self.first_line_indent

            if self.character_index >= len(current_fragment.characters):
                self.character_index = 0
                self.fragment_index += 1
                continue

            character = current_fragment.characters[self.character_index]
            character_width = current_fragment.get_character_width(
                character, self.print_sh, initial_cs=not first_char
            )
            first_char = False

            if character in (NEWLINE, FORM_FEED):
                self.character_index += 1
                if not current_line.fragments:
                    current_line.height = current_font_height * self.line_height
                self._is_first_line = False
                return current_line.manual_break(
                    Align.L if self.align == Align.J else self.align,
                    trailing_nl=character == NEWLINE,
                    trailing_form_feed=character == FORM_FEED,
                )
            if current_line.width + character_width > max_width:
                self._is_first_line = False
                if (
                    character in BREAKING_SPACE_SYMBOLS_STR
                ):  # must come first, always drop a current space.
                    self.character_index += 1
                    return current_line.manual_break(self.align)
                if self.wrapmode == WrapMode.CHAR:
                    # If the line ends with one or more spaces, then we want to get
                    # rid of them so it can be justified correctly.
                    current_line.trim_trailing_spaces()
                    return current_line.manual_break(self.align)
                if current_line.automatic_break_possible():
                    (
                        self.fragment_index,
                        self.character_index,
                        line,
                    ) = current_line.automatic_break(self.align)
                    self.character_index += 1
                    return line
                if idx_last_forced_break == self.character_index:
                    raise FPDFException(
                        "Not enough horizontal space to render a single character"
                    )
                self.idx_last_forced_break = self.character_index
                return current_line.manual_break(
                    Align.L if self.align == Align.J else self.align,
                )

            current_line.add_character(
                character,
                character_width,
                current_fragment,
                self.fragment_index,
                self.character_index,
                current_font_height * self.line_height,
                current_fragment.link,
            )

            self.character_index += 1

        if current_line.width:
            self._is_first_line = False
            return current_line.manual_break(
                Align.L if self.align == Align.J else self.align,
            )
        return None
