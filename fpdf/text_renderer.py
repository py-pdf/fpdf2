import logging
import warnings

from contextlib import contextmanager
from math import isclose
from os.path import splitext
from pathlib import Path
from typing import Iterator, Union

from .bidi import BidiParagraph, auto_detect_base_direction
from .deprecation import get_stack_level
from .drawing import convert_to_device_color
from .errors import FPDFException, FPDFUnicodeEncodingException
from .fonts import CORE_FONTS, CoreFont, FontFace, TextStyle, TTFFont
from .enums import PDFResourceType, TextDirection, TextEmphasis
from .line_break import Fragment, TotalPagesSubstitutionFragment
from .unicode_script import UnicodeScript, get_unicode_script

HERE = Path(__file__).resolve().parent
FPDF_FONT_DIR = HERE / "font"
LOGGER = logging.getLogger(__name__)


class TextRendererMixin:
    """
    Mix-in to be added to FPDF().
    # TODO: add details
    """

    def __init__(self, *args, **kwargs):
        self.fonts = {}  # map font string keys to an instance of CoreFont or TTFFont
        self.core_fonts_encoding = "latin-1"
        "Font encoding, Latin-1 by default"
        # Replace these fonts with these core fonts
        self.font_aliases = {
            "arial": "helvetica",
            "couriernew": "courier",
            "timesnewroman": "times",
        }
        # Graphics state variables defined as properties by GraphicsStateMixin.
        # We set their default values here.
        self.font_family = ""  # current font family
        # current font style (BOLD/ITALICS - does not handle UNDERLINE nor STRIKETHROUGH):
        self.font_style = ""
        self.underline = False
        self.strikethrough = False
        self.font_size_pt = 12  # current font size in points
        self.font_stretching = 100  # current font stretching
        self.char_spacing = 0  # current character spacing
        self.current_font = None  # None or an instance of CoreFont or TTFFont
        self.text_color = self.DEFAULT_TEXT_COLOR
        self._fallback_font_ids = []
        self._fallback_font_exact_match = False
        # pylint: disable=fixme
        # TODO: add self.text_mode + self._record_text_quad_points / ._text_quad_points
        super().__init__(*args, **kwargs)

    @property
    def emphasis(self) -> TextEmphasis:
        "The current text emphasis: bold, italics, underline and/or strikethrough."
        font_style = self.font_style
        if self.strikethrough:
            font_style += "S"
        if self.underline:
            font_style += "U"
        return TextEmphasis.coerce(font_style)

    @property
    def is_ttf_font(self) -> bool:
        return self.current_font and self.current_font.type == "TTF"

    def set_text_color(self, r, g=-1, b=-1):
        """
        Defines the color used for text.
        Accepts either a single greyscale value, 3 values as RGB components, a single `#abc` or `#abcdef` hexadecimal color string,
        or an instance of `fpdf.drawing.DeviceCMYK`, `fpdf.drawing.DeviceRGB` or `fpdf.drawing.DeviceGray`.
        The method can be called before the first page is created and the value is retained from page to page.

        Args:
            r (int, tuple, fpdf.drawing.DeviceGray, fpdf.drawing.DeviceRGB): if `g` and `b` are given, this indicates the red component.
                Else, this indicates the grey level. The value must be between 0 and 255.
            g (int): green component (between 0 and 255)
            b (int): blue component (between 0 and 255)
        """
        self.text_color = convert_to_device_color(r, g, b)

    def set_font_size(self, size):
        """
        Configure the font size in points

        Args:
            size (float): font size in points
        """
        if isclose(self.font_size_pt, size):
            return
        self.font_size_pt = size
        if self.page > 0:
            if not self.current_font:
                raise FPDFException(
                    "Cannot set font size: a font must be selected first"
                )
            self._out(f"BT /F{self.current_font.i} {self.font_size_pt:.2f} Tf ET")
            self._resource_catalog.add(
                PDFResourceType.FONT, self.current_font.i, self.page
            )

    def set_char_spacing(self, spacing):
        """
        Sets horizontal character spacing.
        A positive value increases the space between characters, a negative value
        reduces it (which may result in glyph overlap).
        By default, no spacing is set (which is equivalent to a value of 0).

        Args:
            spacing (float): horizontal spacing in document units
        """
        if self.char_spacing == spacing:
            return
        self.char_spacing = spacing
        if self.page > 0:
            self._out(f"BT {spacing:.2f} Tc ET")

    def set_stretching(self, stretching):
        """
        Sets horizontal font stretching.
        By default, no stretching is set (which is equivalent to a value of 100).

        Args:
            stretching (float): horizontal stretching (scaling) in percents.
        """
        if self.font_stretching == stretching:
            return
        self.font_stretching = stretching
        if self.page > 0:
            self._out(f"BT {stretching:.2f} Tz ET")

    def set_fallback_fonts(self, fallback_fonts, exact_match=True):
        """
        Allows you to specify a list of fonts to be used if any character is not available on the font currently set.
        Detailed documentation: https://py-pdf.github.io/fpdf2/Unicode.html#fallback-fonts

        Args:
            fallback_fonts: sequence of fallback font IDs
            exact_match (bool): when a glyph cannot be rendered uing the current font,
                fpdf2 will look for a fallback font matching the current character emphasis (bold/italics).
                If it does not find such matching font, and `exact_match` is True, no fallback font will be used.
                If it does not find such matching font, and `exact_match` is False, a fallback font will still be used.
                To get even more control over this logic, you can also override `FPDF.get_fallback_font()`
        """
        fallback_font_ids = []
        for fallback_font in fallback_fonts:
            found = False
            for fontkey in self.fonts:
                # will add all font styles on the same family
                if fontkey.replace("B", "").replace("I", "") == fallback_font.lower():
                    fallback_font_ids.append(fontkey)
                    found = True
            if not found:
                raise FPDFException(
                    f"Undefined fallback font: {fallback_font} - Use FPDF.add_font() beforehand"
                )
        self._fallback_font_ids = tuple(fallback_font_ids)
        self._fallback_font_exact_match = exact_match

    @contextmanager
    def use_text_style(self, text_style: TextStyle):
        prev_l_margin = None
        if text_style:
            if text_style.t_margin:
                self.ln(text_style.t_margin)
            if text_style.l_margin:
                if isinstance(text_style.l_margin, (float, int)):
                    prev_l_margin = self.l_margin
                    self.l_margin = text_style.l_margin
                    self.x = self.l_margin
                else:
                    LOGGER.debug(
                        "Unsupported '%s' value provided as l_margin to .use_text_style()",
                        text_style.l_margin,
                    )
        with self.use_font_face(text_style):
            yield
        if text_style and text_style.b_margin:
            self.ln(text_style.b_margin)
        if prev_l_margin is not None:
            self.l_margin = prev_l_margin
            self.x = self.l_margin

    @contextmanager
    def use_font_face(self, font_face: FontFace):
        """
        Sets the provided `fpdf.fonts.FontFace` in a local context,
        then restore font settings back to they were initially.
        This method must be used as a context manager using `with`:

            with pdf.use_font_face(FontFace(emphasis="BOLD", color=255, size_pt=42)):
                put_some_text()

        Known limitation: in case of a page jump in this local context,
        the temporary style may "leak" in the header() & footer().
        """
        if not font_face:
            yield
            return
        prev_font = (self.font_family, self.font_style, self.font_size_pt)
        self.set_font(
            font_face.family or self.font_family,
            (
                font_face.emphasis.style
                if font_face.emphasis is not None
                else self.font_style
            ),
            font_face.size_pt or self.font_size_pt,
        )
        prev_text_color = self.text_color
        if font_face.color is not None and font_face.color != self.text_color:
            self.set_text_color(font_face.color)
        prev_fill_color = self.fill_color
        if font_face.fill_color is not None:
            self.set_fill_color(font_face.fill_color)
        yield
        if font_face.fill_color is not None:
            self.set_fill_color(prev_fill_color)
        self.text_color = prev_text_color
        self.set_font(*prev_font)

    def set_new_page_font_settings(self):
        self.font_family = ""
        self.font_stretching = 100
        self.char_spacing = 0

    def add_font(self, family=None, style="", fname=None, uni="DEPRECATED"):
        """
        Imports a TrueType or OpenType font and makes it available
        for later calls to the `FPDF.set_font()` method.

        You will find more information on the "Unicode" documentation page.

        Args:
            family (str): optional name of the font family. Used as a reference for `FPDF.set_font()`.
                If not provided, use the base name of the `fname` font path, without extension.
            style (str): font style. "" for regular, include 'B' for bold, and/or 'I' for italic.
            fname (str): font file name. You can specify a relative or full path.
                If the file is not found, it will be searched in `FPDF_FONT_DIR`.
            uni (bool): [**DEPRECATED since 2.5.1**] unused
        """
        if not fname:
            raise ValueError('"fname" parameter is required')

        ext = splitext(str(fname))[1].lower()
        if ext not in (".otf", ".otc", ".ttf", ".ttc"):
            raise ValueError(
                f"Unsupported font file extension: {ext}."
                " add_font() used to accept .pkl file as input, but for security reasons"
                " this feature is deprecated since v2.5.1 and has been removed in v2.5.3."
            )

        if uni != "DEPRECATED":
            warnings.warn(
                (
                    '"uni" parameter is deprecated since v2.5.1, '
                    "unused and will soon be removed"
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )

        style = "".join(sorted(style.upper()))
        if any(letter not in "BI" for letter in style):
            raise ValueError(
                f"Unknown style provided (only B & I letters are allowed): {style}"
            )

        for parent in (".", FPDF_FONT_DIR):
            if not parent:
                continue
            if (Path(parent) / fname).exists():
                font_file_path = Path(parent) / fname
                break
        else:
            raise FileNotFoundError(f"TTF Font file not found: {fname}")

        if family is None:
            family = font_file_path.stem

        fontkey = f"{family.lower()}{style}"
        # Check if font already added or one of the core fonts
        if fontkey in self.fonts or fontkey in CORE_FONTS:
            warnings.warn(
                f"Core font or font already added '{fontkey}': doing nothing",
                stacklevel=get_stack_level(),
            )
            return

        self.fonts[fontkey] = TTFFont(self, font_file_path, fontkey, style)

    def set_font(self, family=None, style: Union[str, TextEmphasis] = "", size=0):
        """
        Sets the font used to print character strings.
        It is mandatory to call this method at least once before printing text.

        Default encoding is not specified, but all text writing methods accept only
        unicode for external fonts and one byte encoding for standard.

        Standard fonts use `Latin-1` encoding by default, but Windows
        encoding `cp1252` (Western Europe) can be used with
        `self.core_fonts_encoding = encoding`.

        The font specified is retained from page to page.
        The method can be called before the first page is created.

        Args:
            family (str): name of a font added with `FPDF.add_font`,
                or name of one of the 14 standard "PostScript" fonts:
                Courier (fixed-width), Helvetica (sans serif), Times (serif),
                Symbol (symbolic) or ZapfDingbats (symbolic)
                If an empty string is provided, the current family is retained.
            style (str, fpdf.enums.TextEmphasis): empty string (by default) or a combination
                of one or several letters among B (bold), I (italic), S (strikethrough) and U (underline).
                Bold and italic styles do not apply to Symbol and ZapfDingbats fonts.
            size (float): in points. The default value is the current size.
        """
        if not family:
            family = self.font_family

        family = family.lower()
        if isinstance(style, TextEmphasis):
            style = style.style
        style = "".join(sorted(style.upper()))
        if any(letter not in "BISU" for letter in style):
            raise ValueError(
                f"Unknown style provided (only B/I/S/U letters are allowed): {style}"
            )
        if "U" in style:
            self.underline = True
            style = style.replace("U", "")
        else:
            self.underline = False
        if "S" in style:
            self.strikethrough = True
            style = style.replace("S", "")
        else:
            self.strikethrough = False

        if family in self.font_aliases and family + style not in self.fonts:
            warnings.warn(
                f"Substituting font {family} by core font {self.font_aliases[family]}"
                " - This is deprecated since v2.7.8, and will soon be removed",
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            family = self.font_aliases[family]
        elif family in ("symbol", "zapfdingbats") and style:
            warnings.warn(
                f"Built-in font {family} only has a single 'style' "
                "and can't be bold or italic",
                stacklevel=get_stack_level(),
            )
            style = ""

        if not size:
            size = self.font_size_pt

        # Test if font is already selected
        if (
            self.font_family == family
            and self.font_style == style
            and isclose(self.font_size_pt, size)
        ):
            return

        # Test if used for the first time
        fontkey = family + style
        if fontkey not in self.fonts:
            if fontkey not in CORE_FONTS:
                raise FPDFException(
                    f"Undefined font: {fontkey} - "
                    f"Use built-in fonts or FPDF.add_font() beforehand"
                )
            # If it's one of the core fonts, add it to self.fonts
            self.fonts[fontkey] = CoreFont(len(self.fonts) + 1, fontkey, style)

        # Select it
        self.font_family = family
        self.font_style = style
        self.font_size_pt = size
        self.current_font = self.fonts[fontkey]
        if self.page > 0:
            self._out(f"BT /F{self.current_font.i} {self.font_size_pt:.2f} Tf ET")
            self._resource_catalog.add(
                PDFResourceType.FONT, self.current_font.i, self.page
            )

    def set_text_shaping(
        self,
        use_shaping_engine: bool = True,
        features: dict = None,
        direction: Union[str, TextDirection] = None,
        script: str = None,
        language: str = None,
    ):
        """
        Enable or disable text shaping engine when rendering text.
        If features, direction, script or language are not specified the shaping engine will try
        to guess the values based on the input text.

        Args:
            use_shaping_engine: enable or disable the use of the shaping engine to process the text
            features: a dictionary containing 4 digit OpenType features and whether each feature
                should be enabled or disabled
                example: features={"kern": False, "liga": False}
            direction: the direction the text should be rendered, either "ltr" (left to right)
                or "rtl" (right to left).
            script: a valid OpenType script tag like "arab" or "latn"
            language: a valid OpenType language tag like "eng" or "fra"
        """
        if not use_shaping_engine:
            self.text_shaping = None
            return

        try:
            # pylint: disable=import-outside-toplevel, unused-import
            import uharfbuzz
        except ImportError as exc:
            raise FPDFException(
                "The uharfbuzz package could not be imported, but is required for text shaping. Try: pip install uharfbuzz"
            ) from exc

        #
        # Features must be a dictionary containing opentype features and a boolean flag
        # stating whether the feature should be enabled or disabled.
        #
        # e.g. features={"liga": True, "kern": False}
        #
        # https://harfbuzz.github.io/shaping-opentype-features.html
        #

        if features and not isinstance(features, dict):
            raise FPDFException(
                "Features must be a dictionary. See text shaping documentation"
            )
        if not features:
            features = {}

        # Buffer properties (direction, script and language)
        # if the properties are not provided, Harfbuzz "guessing" logic is used.
        # https://harfbuzz.github.io/setting-buffer-properties.html
        # Valid harfbuzz directions are ltr (left to right), rtl (right to left),
        # ttb (top to bottom) or btt (bottom to top)

        text_direction = None
        if direction:
            text_direction = (
                direction
                if isinstance(direction, TextDirection)
                else TextDirection.coerce(direction)
            )
            if text_direction not in [TextDirection.LTR, TextDirection.RTL]:
                raise FPDFException(
                    "FPDF2 only accept ltr (left to right) or rtl (right to left) directions for now."
                )

        self.text_shaping = {
            "use_shaping_engine": True,
            "features": features,
            "direction": text_direction,
            "script": script,
            "language": language,
            "fragment_direction": None,
            "paragraph_direction": None,
        }

    def get_string_width(self, s, normalized=False, markdown=False):
        """
        Returns the length of a string in user unit. A font must be selected.
        The value is calculated with stretching and spacing.

        Note that the width of a cell has some extra padding added to this width,
        on the left & right sides, equal to the .c_margin property.

        Args:
            s (str): the string whose length is to be computed.
            normalized (bool): whether normalization needs to be performed on the input string.
            markdown (bool): indicates if basic markdown support is enabled
        """
        # normalized is parameter for internal use
        s = s if normalized else self.normalize_text(s)
        w = 0
        for frag in self._preload_bidirectional_text(s, markdown):
            w += frag.get_width()
        return w

    def get_fallback_font(self, char, style=""):
        """
        Returns which fallback font has the requested glyph.
        This method can be overridden to provide more control than the `select_mode` parameter
        of `FPDF.set_fallback_fonts()` provides.
        """
        emphasis = TextEmphasis.coerce(style)
        fonts_with_char = [
            font_id
            for font_id in self._fallback_font_ids
            if ord(char) in self.fonts[font_id].cmap
        ]
        if not fonts_with_char:
            return None
        font_with_matching_emphasis = next(
            (font for font in fonts_with_char if self.fonts[font].emphasis == emphasis),
            None,
        )
        if font_with_matching_emphasis:
            return font_with_matching_emphasis
        if self._fallback_font_exact_match:
            return None
        return fonts_with_char[0]

    def normalize_text(self, text):
        """Check that text input is in the correct format/encoding"""
        # - for TTF unicode fonts: unicode object (utf8 encoding)
        # - for built-in fonts: string instances (encoding: latin-1, cp1252)
        if not self.is_ttf_font and self.core_fonts_encoding:
            try:
                return text.encode(self.core_fonts_encoding).decode("latin-1")
            except UnicodeEncodeError as error:
                raise FPDFUnicodeEncodingException(
                    text_index=error.start,
                    character=text[error.start],
                    font_name=self.font_family + self.font_style,
                ) from error
        return text

    def _preload_bidirectional_text(self, text, markdown):
        """ "
        Break the text into bidirectional segments and preload font styles for each fragment
        """
        if not self.text_shaping:
            return self._preload_font_styles(text, markdown)
        paragraph_direction = (
            self.text_shaping["direction"]
            if self.text_shaping["direction"]
            else auto_detect_base_direction(text)
        )

        paragraph = BidiParagraph(text=text, base_direction=paragraph_direction)
        directional_segments = paragraph.get_bidi_fragments()
        self.text_shaping["paragraph_direction"] = paragraph.base_direction

        fragments = []
        for bidi_text, bidi_direction in directional_segments:
            self.text_shaping["fragment_direction"] = bidi_direction
            fragments += self._preload_font_styles(bidi_text, markdown)
        return tuple(fragments)

    def _preload_font_styles(self, text, markdown):
        """
        When Markdown styling is enabled, we require secondary fonts
        to ender text in bold & italics.
        This function ensure that those fonts are available.
        It needs to perform Markdown parsing,
        so we return the resulting `styled_txt_frags` tuple
        to avoid repeating this processing later on.
        """
        if not text:
            return tuple()
        prev_font_style = self.font_style
        if self.underline:
            prev_font_style += "U"
        if self.strikethrough:
            prev_font_style += "S"
        styled_txt_frags = tuple(self._parse_chars(text, markdown))
        if markdown:
            page = self.page
            # We set the current to page to zero so that
            # set_font() does not produce any text object on the stream buffer:
            self.page = 0
            if any(frag.font_style == "B" for frag in styled_txt_frags):
                # Ensuring bold font is supported:
                self.set_font(style="B")
            if any(frag.font_style == "I" for frag in styled_txt_frags):
                # Ensuring italics font is supported:
                self.set_font(style="I")
            if any(frag.font_style == "BI" for frag in styled_txt_frags):
                # Ensuring bold italics font is supported:
                self.set_font(style="BI")
            if any(frag.font_style == "" for frag in styled_txt_frags):
                # Ensuring base font is supported:
                self.set_font(style="")
            for frag in styled_txt_frags:
                frag.font = self.fonts[frag.font_family + frag.font_style]
            # Restoring initial style:
            self.set_font(style=prev_font_style)
            self.page = page
        return styled_txt_frags

    def _parse_chars(self, text: str, markdown: bool) -> Iterator[Fragment]:
        "Split text into fragments"
        if not markdown and not self.text_shaping and not self._fallback_font_ids:
            if self.str_alias_nb_pages:
                for seq, fragment_text in enumerate(
                    text.split(self.str_alias_nb_pages)
                ):
                    if seq > 0:
                        yield TotalPagesSubstitutionFragment(
                            self.str_alias_nb_pages,
                            self._get_current_graphics_state(),
                            self.k,
                        )
                    if fragment_text:
                        yield Fragment(
                            fragment_text, self._get_current_graphics_state(), self.k
                        )
                return

            yield Fragment(text, self._get_current_graphics_state(), self.k)
            return
        txt_frag, in_bold, in_italics, in_strikethrough, in_underline = (
            [],
            "B" in self.font_style,
            "I" in self.font_style,
            bool(self.strikethrough),
            bool(self.underline),
        )
        current_fallback_font = None
        current_text_script = None

        def frag():
            nonlocal txt_frag, current_fallback_font, current_text_script
            gstate = self._get_current_graphics_state()
            gstate["font_style"] = ("B" if in_bold else "") + (
                "I" if in_italics else ""
            )
            gstate["strikethrough"] = in_strikethrough
            gstate["underline"] = in_underline
            if current_fallback_font:
                gstate["font_family"] = "".join(
                    c for c in current_fallback_font if c.islower()
                )
                gstate["font_style"] = "".join(
                    c for c in current_fallback_font if c.isupper()
                )
                gstate["current_font"] = self.fonts[current_fallback_font]
                current_fallback_font = None
                current_text_script = None
            fragment = Fragment(
                txt_frag,
                gstate,
                self.k,
            )
            txt_frag = []
            return fragment

        if self.is_ttf_font:
            font_glyphs = self.current_font.cmap
        else:
            font_glyphs = []
        num_escape_chars = 0

        while text:
            is_marker = text[:2] in (
                self.MARKDOWN_BOLD_MARKER,
                self.MARKDOWN_ITALICS_MARKER,
                self.MARKDOWN_STRIKETHROUGH_MARKER,
                self.MARKDOWN_UNDERLINE_MARKER,
            )
            half_marker = text[0]
            text_script = get_unicode_script(text[0])
            if text_script not in (
                UnicodeScript.COMMON,
                UnicodeScript.UNKNOWN,
                current_text_script,
            ):
                if txt_frag and current_text_script:
                    yield frag()
                current_text_script = text_script

            if self.str_alias_nb_pages:
                if text[: len(self.str_alias_nb_pages)] == self.str_alias_nb_pages:
                    if txt_frag:
                        yield frag()
                    gstate = self._get_current_graphics_state()
                    gstate["font_style"] = ("B" if in_bold else "") + (
                        "I" if in_italics else ""
                    )
                    gstate["strikethrough"] = in_strikethrough
                    gstate["underline"] = in_underline
                    yield TotalPagesSubstitutionFragment(
                        self.str_alias_nb_pages,
                        gstate,
                        self.k,
                    )
                    text = text[len(self.str_alias_nb_pages) :]
                    continue

            # Check that previous & next characters are not identical to the marker:
            if markdown:
                if (
                    is_marker
                    and (not txt_frag or txt_frag[-1] != half_marker)
                    and (len(text) < 3 or text[2] != half_marker)
                ):
                    txt_frag = (
                        txt_frag[: -((num_escape_chars + 1) // 2)]
                        if num_escape_chars > 0
                        else txt_frag
                    )
                    if num_escape_chars % 2 == 0:
                        if txt_frag:
                            yield frag()
                        if text[:2] == self.MARKDOWN_BOLD_MARKER:
                            in_bold = not in_bold
                        if text[:2] == self.MARKDOWN_ITALICS_MARKER:
                            in_italics = not in_italics
                        if text[:2] == self.MARKDOWN_STRIKETHROUGH_MARKER:
                            in_strikethrough = not in_strikethrough
                        if text[:2] == self.MARKDOWN_UNDERLINE_MARKER:
                            in_underline = not in_underline
                        text = text[2:]
                        continue
                num_escape_chars = (
                    num_escape_chars + 1
                    if text[0] == self.MARKDOWN_ESCAPE_CHARACTER
                    else 0
                )
                is_link = self.MARKDOWN_LINK_REGEX.match(text)
                if is_link:
                    link_text, link_dest, text = is_link.groups()
                    if txt_frag:
                        yield frag()
                    gstate = self._get_current_graphics_state()
                    gstate["underline"] = self.MARKDOWN_LINK_UNDERLINE
                    if self.MARKDOWN_LINK_COLOR:
                        gstate["text_color"] = self.MARKDOWN_LINK_COLOR
                    try:
                        page = int(link_dest)
                        link_dest = self.add_link(page=page)
                    except ValueError:
                        pass
                    yield Fragment(
                        list(link_text),
                        gstate,
                        self.k,
                        link=link_dest,
                    )
                    continue
            if self.is_ttf_font and text[0] != "\n" and not ord(text[0]) in font_glyphs:
                style = ("B" if in_bold else "") + ("I" if in_italics else "")
                fallback_font = self.get_fallback_font(text[0], style)
                if fallback_font:
                    if fallback_font == current_fallback_font:
                        txt_frag.append(text[0])
                        text = text[1:]
                        continue
                    if txt_frag:
                        yield frag()
                    current_fallback_font = fallback_font
                    txt_frag.append(text[0])
                    text = text[1:]
                    continue
            if current_fallback_font:
                if txt_frag:
                    yield frag()
                current_fallback_font = None
            txt_frag.append(text[0])
            text = text[1:]
        if txt_frag:
            yield frag()

    def set_doc_option(self, opt, value):
        """
        Defines a document option.

        Args:
            opt (str): name of the option to set
            value (str) option value

        .. deprecated:: 2.4.0
            Simply set the `FPDF.core_fonts_encoding` property as a replacement.
        """
        warnings.warn(
            (
                "set_doc_option() is deprecated since v2.4.0 "
                "and will be removed in a future release. "
                "Simply set the `.core_fonts_encoding` property as a replacement."
            ),
            DeprecationWarning,
            stacklevel=get_stack_level(),
        )
        if opt != "core_fonts_encoding":
            raise FPDFException(f'Unknown document option "{opt}"')
        self.core_fonts_encoding = value
