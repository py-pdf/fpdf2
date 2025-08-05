"""
HTML renderer

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/HTML.html>
"""

from html.parser import HTMLParser
from string import ascii_lowercase, ascii_uppercase
import logging, re, warnings
from typing import Optional, Union

from .deprecation import get_stack_level
from .drawing import color_from_hex_string, convert_to_device_color
from .enums import Align, TextEmphasis, XPos, YPos
from .errors import FPDFException
from .fonts import FontFace, TextStyle
from .table import Table
from .util import get_scale_factor, int2roman

LOGGER = logging.getLogger(__name__)
MESSAGE_WAITING_WIN1252 = "\x95"  # MESSAGE WAITING character in Windows-1252 encoding
BULLET_UNICODE = "•"  # U+2022
DEGREE_SIGN_WIN1252 = "\xb0"  # DEGREE SIGN character in Windows-1252 encoding
RING_OPERATOR_UNICODE = "∘"  # U+2218
HEADING_TAGS = ("title", "h1", "h2", "h3", "h4", "h5", "h6")
# Some of the margin values below are fractions, in order to be fully backward-compatible,
# and due to the _scale_units() conversion performed in HTML2FPDF constructor below.
# Those constants are formatted as Mixed Fractions, a mathematical representation
# making clear what the closest integer value is.
DEFAULT_TAG_STYLES = {
    # Inline tags are FontFace instances :
    "a": FontFace(color="#00f", emphasis="UNDERLINE"),
    "b": FontFace(emphasis="BOLD"),
    "code": FontFace(family="Courier"),
    "del": FontFace(emphasis="STRIKETHROUGH"),
    "em": FontFace(emphasis="ITALICS"),
    "font": FontFace(),
    "i": FontFace(emphasis="ITALICS"),
    "s": FontFace(emphasis="STRIKETHROUGH"),
    "strong": FontFace(emphasis="BOLD"),
    "u": FontFace(emphasis="UNDERLINE"),
    # Block tags are TextStyle instances :
    "blockquote": TextStyle(color="#64002d", t_margin=3, b_margin=3),
    "center": TextStyle(t_margin=4 + 7 / 30, l_margin=Align.C),
    "dd": TextStyle(l_margin=10),
    "dt": TextStyle(font_style="B", t_margin=4 + 7 / 30),
    "title": TextStyle(  # Only rendered if render_title_tag=True
        b_margin=0.4,
        font_size_pt=30,
        t_margin=6,
        l_margin="Center",
    ),
    "h1": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=24, t_margin=5 + 834 / 900
    ),
    "h2": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=18, t_margin=5 + 453 / 900
    ),
    "h3": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=14, t_margin=5 + 199 / 900
    ),
    "h4": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=12, t_margin=5 + 72 / 900
    ),
    "h5": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=10, t_margin=5 - 55 / 900
    ),
    "h6": TextStyle(
        color="#960000", b_margin=0.4, font_size_pt=8, t_margin=5 - 182 / 900
    ),
    "li": TextStyle(l_margin=5, t_margin=2),
    "p": TextStyle(),
    "pre": TextStyle(t_margin=4 + 7 / 30, font_family="Courier"),
    "ol": TextStyle(t_margin=2),
    "ul": TextStyle(t_margin=2),
}
INLINE_TAGS = ("a", "b", "code", "del", "em", "font", "i", "s", "strong", "u")
BLOCK_TAGS = HEADING_TAGS + (
    "blockquote",
    "center",
    "dd",
    "dt",
    "li",
    "p",
    "pre",
    "ol",
    "ul",
)
# This defensive programming check ensures that we do not forget any tag in the 2 *_TAGS constants above:
assert (set(BLOCK_TAGS) ^ set(INLINE_TAGS)) == set(DEFAULT_TAG_STYLES.keys())

# Pattern to substitute whitespace sequences with a single space character each.
# The following are all Unicode characters with White_Space classification plus the newline.
# The pattern excludes the non-breaking spaces that are included in "\s".
# We also exclude the OGHAM SPACE MARK for now, because while being a word separator,
# it is usually a graphically visible glyph.
_WS_CHARS = "".join(
    (
        # "\u0009",  # CHARACTER TABULATION
        # "\u000a",  # LINE FEED
        # "\u000b",  # LINE TABULATION
        # "\u000c",  # FORM FEED
        # "\u000d",  # CARRIAGE RETURN
        "\u0009-\u000d",  # combine the above
        "\u0020",  # SPACE
        "\u0085",  # NEXT LINE
        # "\u00a0",  # NO-BREAK SPACE   (keep)
        # "\u1680",  # OGHAM SPACE MARK (not actually white)
        # "\u2000",  # EN QUAD
        # "\u2001",  # EM QUAD
        # "\u2002",  # EN SPACE
        # "\u2003",  # EM SPACE
        # "\u2004",  # THREE-PER-EM SPACE
        # "\u2005",  # FOUR-PER-EM SPACE
        # "\u2006",  # SIX-PER-EM SPACE
        # "\u2007",  # FIGURE SPACE
        # "\u2008",  # PUNCTUATION SPACE
        # "\u2009",  # THIN SPACE
        # "\u200a",  # HAIR SPACE
        "\u2000-\u200a",  # combine the above
        "\u2028",  # LINE SEPARATOR
        "\u2029",  # PARAGRAPH SEPARATOR
        # "\u202f",  # NARROW NO-BREAK SPACE (keep)
        "\u205f",  # MEDIUM MATHEMATICAL SPACE
        "\u3000",  # IDEOGRAPHIC SPACE
    )
)
_WS_SUB_PAT = re.compile(f"[{_WS_CHARS}]+")

COLOR_DICT = {
    "black": "#000000",
    "navy": "#000080",
    "darkblue": "#00008b",
    "mediumblue": "#0000cd",
    "blue": "#0000ff",
    "darkgreen": "#006400",
    "green": "#008000",
    "teal": "#008080",
    "darkcyan": "#008b8b",
    "deepskyblue": "#00bfff",
    "darkturquoise": "#00ced1",
    "mediumspringgreen": "#00fa9a",
    "lime": "#00ff00",
    "springgreen": "#00ff7f",
    "aqua": "#00ffff",
    "cyan": "#00ffff",
    "midnightblue": "#191970",
    "dodgerblue": "#1e90ff",
    "lightseagreen": "#20b2aa",
    "forestgreen": "#228b22",
    "seagreen": "#2e8b57",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "limegreen": "#32cd32",
    "mediumseagreen": "#3cb371",
    "turquoise": "#40e0d0",
    "royalblue": "#4169e1",
    "steelblue": "#4682b4",
    "darkslateblue": "#483d8b",
    "mediumturquoise": "#48d1cc",
    "indigo": "#4b0082",
    "darkolivegreen": "#556b2f",
    "cadetblue": "#5f9ea0",
    "cornflowerblue": "#6495ed",
    "rebeccapurple": "#663399",
    "mediumaquamarine": "#66cdaa",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "slateblue": "#6a5acd",
    "olivedrab": "#6b8e23",
    "slategray": "#708090",
    "slategrey": "#708090",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "mediumslateblue": "#7b68ee",
    "lawngreen": "#7cfc00",
    "chartreuse": "#7fff00",
    "aquamarine": "#7fffd4",
    "maroon": "#800000",
    "purple": "#800080",
    "olive": "#808000",
    "gray": "#808080",
    "grey": "#808080",
    "skyblue": "#87ceeb",
    "lightskyblue": "#87cefa",
    "blueviolet": "#8a2be2",
    "darkred": "#8b0000",
    "darkmagenta": "#8b008b",
    "saddlebrown": "#8b4513",
    "darkseagreen": "#8fbc8f",
    "lightgreen": "#90ee90",
    "mediumpurple": "#9370db",
    "darkviolet": "#9400d3",
    "palegreen": "#98fb98",
    "darkorchid": "#9932cc",
    "yellowgreen": "#9acd32",
    "sienna": "#a0522d",
    "brown": "#a52a2a",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "lightblue": "#add8e6",
    "greenyellow": "#adff2f",
    "paleturquoise": "#afeeee",
    "lightsteelblue": "#b0c4de",
    "powderblue": "#b0e0e6",
    "firebrick": "#b22222",
    "darkgoldenrod": "#b8860b",
    "mediumorchid": "#ba55d3",
    "rosybrown": "#bc8f8f",
    "darkkhaki": "#bdb76b",
    "silver": "#c0c0c0",
    "mediumvioletred": "#c71585",
    "indianred": "#cd5c5c",
    "peru": "#cd853f",
    "chocolate": "#d2691e",
    "tan": "#d2b48c",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "thistle": "#d8bfd8",
    "orchid": "#da70d6",
    "goldenrod": "#daa520",
    "palevioletred": "#db7093",
    "crimson": "#dc143c",
    "gainsboro": "#dcdcdc",
    "plum": "#dda0dd",
    "burlywood": "#deb887",
    "lightcyan": "#e0ffff",
    "lavender": "#e6e6fa",
    "darksalmon": "#e9967a",
    "violet": "#ee82ee",
    "palegoldenrod": "#eee8aa",
    "lightcoral": "#f08080",
    "khaki": "#f0e68c",
    "aliceblue": "#f0f8ff",
    "honeydew": "#f0fff0",
    "azure": "#f0ffff",
    "sandybrown": "#f4a460",
    "wheat": "#f5deb3",
    "beige": "#f5f5dc",
    "whitesmoke": "#f5f5f5",
    "mintcream": "#f5fffa",
    "ghostwhite": "#f8f8ff",
    "salmon": "#fa8072",
    "antiquewhite": "#faebd7",
    "linen": "#faf0e6",
    "lightgoldenrodyellow": "#fafad2",
    "oldlace": "#fdf5e6",
    "red": "#ff0000",
    "fuchsia": "#ff00ff",
    "magenta": "#ff00ff",
    "deeppink": "#ff1493",
    "orangered": "#ff4500",
    "tomato": "#ff6347",
    "hotpink": "#ff69b4",
    "coral": "#ff7f50",
    "darkorange": "#ff8c00",
    "lightsalmon": "#ffa07a",
    "orange": "#ffa500",
    "lightpink": "#ffb6c1",
    "pink": "#ffc0cb",
    "gold": "#ffd700",
    "peachpuff": "#ffdab9",
    "navajowhite": "#ffdead",
    "moccasin": "#ffe4b5",
    "bisque": "#ffe4c4",
    "mistyrose": "#ffe4e1",
    "blanchedalmond": "#ffebcd",
    "papayawhip": "#ffefd5",
    "lavenderblush": "#fff0f5",
    "seashell": "#fff5ee",
    "cornsilk": "#fff8dc",
    "lemonchiffon": "#fffacd",
    "floralwhite": "#fffaf0",
    "snow": "#fffafa",
    "yellow": "#ffff00",
    "lightyellow": "#ffffe0",
    "ivory": "#fffff0",
    "white": "#ffffff",
}


def color_as_decimal(color="#000000"):
    """
    Convert a web color name to a (R, G, B) color tuple.
    cf. https://en.wikipedia.org/wiki/Web_colors#HTML_color_names
    """
    if not color:
        return None
    # Checks if color is a name and gets the hex value
    hexcolor = COLOR_DICT.get(color.lower(), color)
    return color_from_hex_string(hexcolor)


def parse_css_style(style_attr):
    """Parse `style="..."` HTML attributes, and return a dict of key-value"""
    style = {}
    for element in style_attr.split(";"):
        if not element:
            continue
        pair = element.split(":")
        if len(pair) == 2 and pair[0] and pair[1]:
            attr, value = pair
            style[attr.strip()] = value.strip()
    return style


class HTML2FPDF(HTMLParser):
    "Render basic HTML to FPDF"

    HTML_UNCLOSED_TAGS = ("br", "dd", "dt", "hr", "img", "li", "td", "tr")
    TABLE_LINE_HEIGHT = 1.3

    def __init__(
        self,
        pdf,
        image_map=None,
        li_tag_indent=None,
        dd_tag_indent=None,
        table_line_separators=False,
        ul_bullet_char="disc",
        li_prefix_color=(190, 0, 0),
        heading_sizes=None,
        pre_code_font=None,
        warn_on_tags_not_matching=True,
        tag_indents=None,
        tag_styles=None,
        font_family="times",
        render_title_tag=False,
    ):
        """
        Args:
            pdf (fpdf.fpdf.FPDF): an instance of `FPDF`
            image_map (function): an optional one-argument function that map `<img>` "src" to new image URLs
            li_tag_indent (int): [**DEPRECATED since v2.7.9**]
                numeric indentation of `<li>` elements - Set `tag_styles` instead
            dd_tag_indent (int): [**DEPRECATED since v2.7.9**]
                numeric indentation of `<dd>` elements - Set `tag_styles` instead
            table_line_separators (bool): enable horizontal line separators in `<table>`. Defaults to `False`.
            ul_bullet_char (str): bullet character preceding `<li>` items in `<ul>` lists.
                You can also specify special bullet names like `"circle"` or `"disc"` (the default).
                Can also be configured using the HTML `type` attribute of `<ul>` tags.
            li_prefix_color (tuple, str, fpdf.drawing.DeviceCMYK, fpdf.drawing.DeviceGray, fpdf.drawing.DeviceRGB): color for bullets
                or numbers preceding `<li>` tags. This applies to both `<ul>` & `<ol>` lists.
            heading_sizes (dict): [**DEPRECATED since v2.7.9**]
                font size per heading level names ("h1", "h2"...) - Set `tag_styles` instead
            pre_code_font (str): [**DEPRECATED since v2.7.9**]
                font to use for `<pre>` & `<code>` blocks - Set `tag_styles` instead
            warn_on_tags_not_matching (bool): control warnings production for unmatched HTML tags. Defaults to `True`.
            tag_indents (dict): [**DEPRECATED since v2.8.0**]
                mapping of HTML tag names to numeric values representing their horizontal left indentation. - Set `tag_styles` instead
            tag_styles (dict[str, fpdf.fonts.TextStyle]): mapping of HTML tag names to `fpdf.TextStyle` or `fpdf.FontFace` instances
            font_family (str): optional font family. Default to Times.
            render_title_tag (bool): Render the document <title> at the beginning of the PDF. Default to False.
        """
        super().__init__()
        self.pdf = pdf
        self.image_map = image_map or (lambda src: src)
        self.ul_bullet_char = ul_bullet_char
        self.li_prefix_color = (
            color_as_decimal(li_prefix_color)
            if isinstance(li_prefix_color, str)
            else convert_to_device_color(li_prefix_color)
        )
        self.warn_on_tags_not_matching = warn_on_tags_not_matching
        # The following 4 attributes are there to serve as "temporary state",
        # so that changes to those settings are saved,
        # but not reflected onto self.pdf yet,
        # and only "effectively" applied when self._write_paragraph() is called.
        # This way, we often avoid useless operators in the PDF content stream.
        self.font_family = pdf.font_family or font_family
        self.font_size_pt = pdf.font_size_pt
        self.font_emphasis = TextEmphasis.NONE
        self.font_color = pdf.text_color
        # For historical / backward-compatibility reasons,
        # write_html() sets an active font (Times by default):
        self.pdf.set_font(
            family=self.font_family,
            size=self.font_size_pt,
            style=self.font_emphasis.style,
        )
        self.style_stack = []  # list of FontFace
        self._page_break_after_paragraph = False
        self.follows_trailing_space = False  # The last write has ended with a space.
        self.follows_heading = False  # We don't want extra space below a heading.
        self.align: Optional[Union[float, Align]] = None
        self.heading_level = None
        self._tags_stack = []
        self._column = self.pdf.text_columns(skip_leading_spaces=True)
        self._paragraph = self._column.paragraph()
        # <pre>-related properties:
        self._pre_formatted = False  # preserve whitespace while True.
        # nothing written yet to <pre>, remove one initial nl:
        self._pre_started = False
        # <a>-related properties:
        self.href = ""
        # <ul>/<ol>-related properties:
        self.indent = 0
        self.line_height_stack = []
        self.ol_type = {}  # when inside a <ol> tag, can be "a", "A", "i", "I" or "1"
        self.bullet = []
        # <title>-related properties:
        self.render_title_tag = render_title_tag
        self._in_title = False
        # <table>-related properties:
        self.table_line_separators = table_line_separators
        self.table = None  # becomes a Table instance when processing <table> tags
        self.table_row = None  # becomes a Row instance when processing <tr> tags
        self.tr = None  # becomes a dict of attributes when processing <tr> tags
        self.td_th = None  # becomes a dict of attributes when processing <td>/<th> tags
        #                    "inserted" is a special attribute indicating that a cell has be inserted in self.table_row

        self.tag_styles = _scale_units(pdf, DEFAULT_TAG_STYLES)
        for tag, tag_style in (tag_styles or {}).items():
            if tag not in DEFAULT_TAG_STYLES:
                raise NotImplementedError(
                    f"Cannot set style for HTML tag <{tag}> (contributions are welcome to add support for this)"
                )
            if not isinstance(tag_style, FontFace):
                raise ValueError(
                    f"tag_styles values must be instances of FontFace or TextStyle - received: {tag_style}"
                )
            # We convert FontFace values provided for block tags into TextStyle values:
            if tag in BLOCK_TAGS and not isinstance(tag_style, TextStyle):
                # pylint: disable=redefined-loop-name
                tag_style = TextStyle(
                    font_family=tag_style.family,
                    font_style=(
                        "" if not tag_style.emphasis else tag_style.emphasis.style
                    ),
                    font_size_pt=tag_style.size_pt,
                    color=tag_style.color,
                    fill_color=tag_style.fill_color,
                    # Using default tag margins:
                    t_margin=self.tag_styles[tag].t_margin,
                    l_margin=self.tag_styles[tag].l_margin,
                    b_margin=self.tag_styles[tag].b_margin,
                )
            self.tag_styles[tag] = tag_style
        if heading_sizes is not None:
            warnings.warn(
                (
                    "The heading_sizes parameter is deprecated since v2.7.9 "
                    "and will be removed in a future release. "
                    "Set the `tag_styles` parameter instead."
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            for tag, size in heading_sizes.items():
                self.tag_styles[tag] = self.tag_styles[tag].replace(font_size_pt=size)
        if pre_code_font is not None:
            warnings.warn(
                (
                    "The pre_code_font parameter is deprecated since v2.7.9 "
                    "and will be removed in a future release. "
                    "Set the `tag_styles` parameter instead."
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            self.tag_styles["code"] = self.tag_styles["code"].replace(
                family=pre_code_font
            )
            self.tag_styles["pre"] = self.tag_styles["pre"].replace(
                font_family=pre_code_font
            )
        if dd_tag_indent is not None:
            warnings.warn(
                (
                    "The dd_tag_indent parameter is deprecated since v2.7.9 "
                    "and will be removed in a future release. "
                    "Set the `tag_styles` parameter instead."
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            self.tag_styles["dd"] = self.tag_styles["dd"].replace(
                l_margin=dd_tag_indent
            )
        if li_tag_indent is not None:
            warnings.warn(
                (
                    "The li_tag_indent parameter is deprecated since v2.7.9 "
                    "and will be removed in a future release. "
                    "Set the `tag_styles` parameter instead."
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            self.tag_styles["li"] = self.tag_styles["li"].replace(
                l_margin=li_tag_indent
            )
        if tag_indents:
            warnings.warn(
                (
                    "The tag_indents parameter is deprecated since v2.8.0 "
                    "and will be removed in a future release. "
                    "Set the `tag_styles` parameter instead."
                ),
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
            for tag, indent in tag_indents.items():
                if tag not in self.tag_styles:
                    raise NotImplementedError(
                        f"Cannot set style for HTML tag <{tag}> (contributions are welcome to add support for this)"
                    )
                self.tag_styles[tag] = self.tag_styles[tag].replace(l_margin=indent)

    def _new_paragraph(
        self,
        align: Optional[Union[float, Align]] = None,
        line_height=1.0,
        top_margin=0,
        bottom_margin=0,
        indent=0,
        bullet="",
    ):
        # Note that currently top_margin is ignored if bullet is also provided,
        # due to the behaviour of TextRegion._render_column_lines()
        self._end_paragraph()
        self.align = align
        if isinstance(indent, Align):
            # Explicit alignment takes priority over alignment provided as TextStyle.l_margin:
            if not self.align:
                self.align = indent
            indent = 0
        if not top_margin and not self.follows_heading:
            top_margin = self.font_size_pt / self.pdf.k
        self._paragraph = self._column.paragraph(
            text_align=self.align,
            line_height=line_height,
            skip_leading_spaces=True,
            top_margin=top_margin,
            bottom_margin=bottom_margin,
            indent=indent,
            bullet_string=bullet,
        )
        self.follows_trailing_space = True
        self.follows_heading = False

    def _end_paragraph(self):
        self.align = None
        if not self._paragraph:
            return
        self._column.end_paragraph()
        self._column.render()
        self._paragraph = None
        self.follows_trailing_space = True
        if self._page_break_after_paragraph:
            # pylint: disable=protected-access
            self.pdf._perform_page_break()
            self._page_break_after_paragraph = False

    def _write_paragraph(self, text, link=None):
        if not text:
            return
        if not self._paragraph:
            self._new_paragraph()
        # The following local stack is required
        # in order for FPDF._get_current_graphics_state()
        # to properly capture the current graphics state,
        # and then to be able to drop those temporary changes,
        # because they will only be "effectively" applied in .end_paragraph().
        # pylint: disable=protected-access
        self.pdf._push_local_stack()
        prev_page = self.pdf.page
        self.pdf.page = 0
        self.pdf.set_font(
            family=self.font_family,
            size=self.font_size_pt,
            style=self.font_emphasis.style,
        )
        if self.font_color != self.pdf.text_color:
            self.pdf.set_text_color(self.font_color)
        self._paragraph.write(text, link=link)
        self.pdf.page = prev_page
        self.pdf._pop_local_stack()

    def _ln(self, h=None):
        if self._paragraph:
            self._paragraph.ln(h=h)
        else:
            self._column.ln(h=h)
        self.follows_trailing_space = True

    def handle_data(self, data):
        if self._in_title:
            if self.pdf.title:
                LOGGER.warning('Ignoring repeated <title> "%s"', data)
            else:
                self.pdf.set_title(data)
            if not self.render_title_tag:
                return
        if self.td_th is not None:
            data = data.strip()
            if not data:
                return
            if "inserted" in self.td_th:
                td_th_tag = self.td_th["tag"]
                raise NotImplementedError(
                    f"Unsupported nested HTML tags inside <{td_th_tag}> element: <{self._tags_stack[-1]}>"
                )
                # We could potentially support nested <b> / <em> / <font> tags
                # by building a list of Fragment instances from the HTML cell content
                # and then passing those fragments to Row.cell().
                # However there should be an incoming refactoring of this code
                # dedicated to text layout, and we should probably wait for that
                # before supporting this feature.
            align = self.td_th.get("align", self.tr.get("align"))
            if align:
                align = align.upper()
            bgcolor = color_as_decimal(
                self.td_th.get("bgcolor", self.tr.get("bgcolor", None))
            )
            colspan = int(self.td_th.get("colspan", "1"))
            rowspan = int(self.td_th.get("rowspan", "1"))
            emphasis = 0
            if self.td_th.get("b"):
                emphasis |= TextEmphasis.B
            if self.td_th.get("i"):
                emphasis |= TextEmphasis.I
            if self.td_th.get("U"):
                emphasis |= TextEmphasis.U
            font_family = (
                self.font_family if self.font_family != self.pdf.font_family else None
            )
            font_size_pt = (
                self.font_size_pt
                if self.font_size_pt != self.pdf.font_size_pt
                else None
            )
            font_style = None
            if font_family or emphasis or font_size_pt or bgcolor:
                font_style = FontFace(
                    family=font_family,
                    emphasis=emphasis,
                    size_pt=font_size_pt,
                    color=self.pdf.text_color,
                    fill_color=bgcolor,
                )
            self.table_row.cell(
                text=data,
                align=align,
                style=font_style,
                colspan=colspan,
                rowspan=rowspan,
            )
            self.td_th["inserted"] = True
        elif self.table is not None:
            # ignore anything else than td inside a table
            pass
        elif self._pre_formatted:  # pre blocks
            # If we want to mimic the exact HTML semantics about newlines at the
            # beginning and end of the block, then this needs some more thought.
            if data.startswith("\n") and self._pre_started:
                if data.endswith("\n"):
                    data = data[1:-1]
                else:
                    data = data[1:]
            self._pre_started = False
            self._write_data(data)
        else:
            data = _WS_SUB_PAT.sub(" ", data)
            if self.follows_trailing_space and data[0] == " ":
                self._write_data(data[1:])
            else:
                self._write_data(data)
            self.follows_trailing_space = data[-1] == " "
        if self._page_break_after_paragraph:
            self._end_paragraph()

    def _write_data(self, data):
        if self.href:
            self.put_link(data)
        else:
            if self.heading_level:
                if self.pdf.section_title_styles:
                    raise NotImplementedError(
                        "Combining write_html() & section styles is currently not supported."
                        " You can open up an issue on github.com/py-pdf/fpdf2 if this is something you would like to see implemented."
                    )
                self.pdf.start_section(data, self.heading_level - 1, strict=False)
            self._write_paragraph(data)

    def handle_starttag(self, tag, attrs):
        self._pre_started = False
        attrs = dict(attrs)
        css_style = parse_css_style(attrs.get("style", ""))
        self._tags_stack.append(tag)
        if css_style.get("break-before") == "page":
            self._end_paragraph()
            # pylint: disable=protected-access
            self.pdf._perform_page_break()
        if tag in ("b", "i", "u") and self.td_th is not None:
            self.td_th[tag] = True
        if tag == "a":
            self.href = attrs["href"]
            try:
                page = int(self.href)
                self.href = self.pdf.add_link(page=page)
            except ValueError:
                pass
        if tag == "br":
            self._write_paragraph("\n")
        if tag == "hr":
            self._end_paragraph()
            width = css_style.get("width", attrs.get("width"))
            if width:
                if width[-1] == "%":
                    width = self.pdf.epw * int(width[:-1]) / 100
                else:
                    width = int(width) / self.pdf.k
            else:
                width = self.pdf.epw
            # Centering:
            x_start = self.pdf.l_margin + (self.pdf.epw - width) / 2
            self.pdf.line(
                x1=x_start,
                y1=self.pdf.y,
                x2=x_start + width,
                y2=self.pdf.y,
            )
            self._write_paragraph("\n")
        if tag == "p":
            self.style_stack.append(
                FontFace(
                    family=self.font_family,
                    emphasis=self.font_emphasis,
                    size_pt=self.font_size_pt,
                    color=self.font_color,
                )
            )
            align = None
            if "align" in attrs:
                align = attrs.get("align")[0].upper()
                if not align in ["L", "R", "J", "C"]:
                    align = None
            line_height = css_style.get("line-height", attrs.get("line-height"))
            # "line-height" attributes are not valid in HTML,
            # but we support it for backward compatibility,
            # because fpdf2 honors it since 2.6.1 and PR #629
            if line_height:
                try:
                    # YYY parse and convert non-float line_height values
                    line_height = float(line_height)
                except ValueError:
                    line_height = None
            tag_style = self.tag_styles[tag]
            if tag_style.color is not None and tag_style.color != self.font_color:
                self.font_color = tag_style.color
            if tag_style.family is not None and tag_style.family != self.font_family:
                self.font_family = tag_style.family
            if tag_style.size_pt is not None and tag_style.size_pt != self.font_size_pt:
                self.font_size_pt = tag_style.size_pt
            if tag_style.emphasis:
                self.font_emphasis |= tag_style.emphasis
            self._new_paragraph(
                align=align,
                line_height=line_height,
                top_margin=tag_style.t_margin,
                bottom_margin=tag_style.b_margin,
                indent=tag_style.l_margin,
            )
        if tag in HEADING_TAGS:
            self.style_stack.append(
                FontFace(
                    family=self.font_family,
                    emphasis=self.font_emphasis,
                    size_pt=self.font_size_pt,
                    color=self.font_color,
                )
            )
            self.heading_level = 0 if tag == "title" else int(tag[1:])
            tag_style = self.tag_styles[tag]
            hsize = (tag_style.size_pt or self.font_size_pt) / self.pdf.k
            if attrs:
                align = attrs.get("align")
                if not align in ["L", "R", "J", "C"]:
                    align = None
            else:
                align = None
            self._new_paragraph(
                align=align,
                top_margin=tag_style.t_margin,
                bottom_margin=tag_style.b_margin * hsize,
                indent=tag_style.l_margin,
            )
            if "color" in css_style:
                self.font_color = color_as_decimal(css_style["color"])
            elif "color" in attrs:
                # "color" attributes are not valid in HTML,
                # but we support it for backward compatibility:
                self.font_color = color_as_decimal(attrs["color"])
            elif tag_style.color is not None and tag_style.color != self.font_color:
                self.font_color = tag_style.color
            if tag_style.family is not None and tag_style.family != self.font_family:
                self.font_family = tag_style.family
            if tag_style.size_pt is not None and tag_style.size_pt != self.font_size_pt:
                self.font_size_pt = tag_style.size_pt
            if tag_style.emphasis:
                self.font_emphasis |= tag_style.emphasis
        if tag in (
            "b",
            "blockquote",
            "center",
            "code",
            "del",
            "em",
            "i",
            "dd",
            "dt",
            "pre",
            "s",
            "strong",
            "u",
        ):
            if tag in BLOCK_TAGS:
                self._end_paragraph()
            self.style_stack.append(
                FontFace(
                    family=self.font_family,
                    emphasis=self.font_emphasis,
                    size_pt=self.font_size_pt,
                    color=self.font_color,
                )
            )
            tag_style = self.tag_styles[tag]
            if tag_style.color:
                self.font_color = tag_style.color
            self.font_family = tag_style.family or self.font_family
            self.font_size_pt = tag_style.size_pt or self.font_size_pt
            if tag_style.emphasis:
                self.font_emphasis |= tag_style.emphasis
            if tag == "pre":
                self._pre_formatted = True
                self._pre_started = True
            if tag in BLOCK_TAGS:
                if tag == "dd":
                    # Not compliant with the HTML spec, but backward-compatible
                    # cf. https://github.com/py-pdf/fpdf2/pull/1217#discussion_r1666643777
                    self.follows_heading = True
                self._new_paragraph(
                    line_height=(
                        self.line_height_stack[-1] if self.line_height_stack else None
                    ),
                    top_margin=tag_style.t_margin,
                    bottom_margin=tag_style.b_margin,
                    indent=tag_style.l_margin,
                )
        if tag == "ul":
            self.indent += 1
            bullet_char = attrs.get("type", self.ul_bullet_char)
            self.bullet.append(bullet_char)
            line_height = css_style.get("line-height", attrs.get("line-height"))
            # "line-height" attributes are not valid in HTML,
            # but we support it for backward compatibility,
            # because fpdf2 honors it since 2.6.1 and PR #629
            if line_height:
                try:
                    # YYY parse and convert non-float line_height values
                    self.line_height_stack.append(float(line_height))
                except ValueError:
                    pass
            else:
                self.line_height_stack.append(None)
            if self.indent == 1:
                tag_style = self.tag_styles[tag]
                self._new_paragraph(
                    line_height=0,
                    top_margin=tag_style.t_margin,
                    bottom_margin=tag_style.b_margin,
                    indent=tag_style.l_margin,
                )
                self._write_paragraph("\u00a0")
            self._end_paragraph()
        if tag == "ol":
            self.indent += 1
            start = int(attrs["start"]) if "start" in attrs else 1
            self.bullet.append(start - 1)
            self.ol_type[self.indent] = attrs.get("type", "1")
            line_height = css_style.get("line-height", attrs.get("line-height"))
            # "line-height" attributes are not valid in HTML,
            # but we support it for backward compatibility,
            # because fpdf2 honors it since 2.6.1 and PR #629
            if line_height:
                try:
                    # YYY parse and convert non-float line_height values
                    self.line_height_stack.append(float(line_height))
                except ValueError:
                    pass
            else:
                self.line_height_stack.append(None)
            if self.indent == 1:
                tag_style = self.tag_styles[tag]
                self._new_paragraph(
                    line_height=0,
                    top_margin=tag_style.t_margin,
                    bottom_margin=tag_style.b_margin,
                    indent=tag_style.l_margin,
                )
                self._write_paragraph("\u00a0")
            self._end_paragraph()
        if tag == "li":
            prev_text_color = self.pdf.text_color
            self.pdf.text_color = self.li_prefix_color
            if self.bullet:
                bullet = self.bullet[self.indent - 1]
            else:
                # Allow <li> to be used outside of <ul> or <ol>.
                bullet = self.ul_bullet_char
            if not isinstance(bullet, int):
                bullet = ul_prefix(bullet, self.pdf.is_ttf_font)
            if not isinstance(bullet, str):
                bullet += 1
                self.bullet[self.indent - 1] = bullet
                ol_type = self.ol_type[self.indent]
                bullet = f"{ol_prefix(ol_type, bullet)}."
            tag_style = self.tag_styles[tag]
            self._ln(tag_style.t_margin)
            self._new_paragraph(
                line_height=(
                    self.line_height_stack[-1] if self.line_height_stack else None
                ),
                indent=tag_style.l_margin * self.indent,
                bottom_margin=tag_style.b_margin,
                bullet=bullet,
            )
            self.pdf.text_color = prev_text_color
        if tag == "font":
            self.style_stack.append(
                FontFace(
                    family=self.font_family,
                    emphasis=self.font_emphasis,
                    size_pt=self.font_size_pt,
                    color=self.font_color,
                )
            )
            if "color" in attrs:
                self.font_color = color_as_decimal(attrs["color"])
            if "font-size" in css_style:
                self.font_size_pt = int(css_style.get("font-size"))
            elif "size" in attrs:
                self.font_size_pt = int(attrs.get("size"))
            if "face" in attrs:
                self.font_family = attrs.get("face").lower()
        if tag == "table":
            self._end_paragraph()
            width = css_style.get("width", attrs.get("width"))
            if width:
                if width[-1] == "%":
                    width = self.pdf.epw * int(width[:-1]) / 100
                else:
                    width = int(width) / self.pdf.k
            if "border" not in attrs:  # default borders
                borders_layout = (
                    "HORIZONTAL_LINES"
                    if self.table_line_separators
                    else "SINGLE_TOP_LINE"
                )
            elif int(attrs["border"]):  # explicitly enabled borders
                borders_layout = (
                    "ALL" if self.table_line_separators else "NO_HORIZONTAL_LINES"
                )
            else:  # explicitly disabled borders
                borders_layout = "NONE"
            align = attrs.get("align", "center").upper()
            padding = float(attrs["cellpadding"]) if "cellpadding" in attrs else None
            spacing = float(attrs.get("cellspacing", 0))
            self.table = Table(
                self.pdf,
                align=align,
                borders_layout=borders_layout,
                line_height=self.font_size_pt / self.pdf.k * self.TABLE_LINE_HEIGHT,
                width=width,
                padding=padding,
                gutter_width=spacing,
                gutter_height=spacing,
            )
            self._ln()
        if tag == "tr":
            if not self.table:
                raise FPDFException("Invalid HTML: <tr> used outside any <table>")
            self.tr = {k.lower(): v for k, v in attrs.items()}
            self.table_row = self.table.row()
        if tag in ("td", "th"):
            if not self.table_row:
                raise FPDFException(f"Invalid HTML: <{tag}> used outside any <tr>")
            self.td_th = {k.lower(): v for k, v in attrs.items()}
            self.td_th["tag"] = tag
            if tag == "th":
                if "align" not in self.td_th:
                    self.td_th["align"] = "CENTER"
                self.td_th["b"] = True
            elif len(self.table.rows) == 1 and not self.table_row.cells:
                # => we are in the 1st <tr>, and the 1st cell is a <td>
                # => we do not treat the first row as a header
                # pylint: disable=protected-access
                self.table._first_row_as_headings = False
                self.table._num_heading_rows = 0
            if "height" in attrs:
                LOGGER.warning(
                    'Ignoring unsupported height="%s" specified on a <%s>',
                    attrs["height"],
                    tag,
                )
            if "width" in attrs:
                width = attrs["width"]
                # pylint: disable=protected-access
                if len(self.table.rows) == 1:  # => first table row
                    if width[-1] == "%":
                        width = width[:-1]
                    if not self.table._col_widths:
                        self.table._col_widths = []
                    self.table._col_widths.append(int(width))
                else:
                    LOGGER.warning(
                        'Ignoring width="%s" specified on a <%s> that is not in the first <tr>',
                        width,
                        tag,
                    )
        if tag == "img" and "src" in attrs:
            width = int(attrs.get("width", 0)) / self.pdf.k
            height = int(attrs.get("height", 0)) / self.pdf.k
            if self.table_row:  # => <img> in a <table>
                if width or height:
                    LOGGER.warning(
                        'Ignoring unsupported "width" / "height" set on <img> element'
                    )
                if self.align:
                    LOGGER.warning("Ignoring unsupported <img> alignment")
                self.table_row.cell(img=attrs["src"], img_fill_width=True)
                self.td_th["inserted"] = True
                return
            x = self.pdf.get_x()
            if self.align:
                x = self.align
            self.pdf.image(
                self.image_map(attrs["src"]), x=x, w=width, h=height, link=self.href
            )
        if tag == "toc":
            self._end_paragraph()
            self.pdf.insert_toc_placeholder(
                self.render_toc, pages=int(attrs.get("pages", 1))
            )
        if tag == "sup":
            self.pdf.char_vpos = "SUP"
        if tag == "sub":
            self.pdf.char_vpos = "SUB"
        if tag == "title":
            self._in_title = True
        if css_style.get("break-after") == "page":
            if tag in ("br", "hr", "img"):
                self._end_paragraph()
                # pylint: disable=protected-access
                self.pdf._perform_page_break()
            else:
                self._page_break_after_paragraph = True

    def handle_endtag(self, tag):
        while (
            self._tags_stack
            and tag != self._tags_stack[-1]
            and self._tags_stack[-1] in self.HTML_UNCLOSED_TAGS
        ):
            self._tags_stack.pop()
        if not self._tags_stack:
            if self.warn_on_tags_not_matching:
                LOGGER.warning(
                    "Unexpected HTML end tag </%s>, start tag may be missing?", tag
                )
        elif tag == self._tags_stack[-1]:
            self._tags_stack.pop()
        elif self.warn_on_tags_not_matching:
            LOGGER.warning(
                "Unexpected HTML end tag </%s>, start tag was <%s>",
                tag,
                self._tags_stack[-1],
            )
        if tag == "a":
            self.href = ""
        if tag == "p":
            if self.style_stack:
                font_face = self.style_stack.pop()
                self.font_family = font_face.family or self.font_family
                self.font_size_pt = font_face.size_pt or self.font_size_pt
                self.font_emphasis = font_face.emphasis
                self.font_color = font_face.color
            self._end_paragraph()
            self.align = None
        if tag in HEADING_TAGS:
            self.heading_level = None
            if self.style_stack:
                font_face = self.style_stack.pop()
                self.font_family = font_face.family or self.font_family
                self.font_size_pt = font_face.size_pt or self.font_size_pt
                self.font_emphasis = font_face.emphasis
                self.font_color = font_face.color
            self._end_paragraph()
            self.follows_heading = True  # We don't want extra space below a heading.
        if tag in (
            "b",
            "blockquote",
            "center",
            "code",
            "em",
            "i",
            "dd",
            "dt",
            "pre",
            "s",
            "strong",
            "u",
        ):
            if self.style_stack:
                font_face = self.style_stack.pop()
                self.font_family = font_face.family or self.font_family
                self.font_size_pt = font_face.size_pt or self.font_size_pt
                self.font_emphasis = font_face.emphasis
                self.font_color = font_face.color
            if tag == "pre":
                self._pre_formatted = False
                self._pre_started = False
            if tag in BLOCK_TAGS:
                self._end_paragraph()
        if tag in ("ul", "ol"):
            self._end_paragraph()
            if tag == "ol":
                self.ol_type.pop(self.indent)
            self.indent -= 1
            self.line_height_stack.pop()
            self.bullet.pop()
        if tag == "table":
            self.table.render()
            self.table = None
            self._ln()
        if tag == "tr":
            self.tr = None
            self.table_row = None
        if tag in ("td", "th"):
            if "inserted" not in self.td_th:
                # handle_data() was not called => we call it to produce an empty cell:
                bgcolor = color_as_decimal(
                    self.td_th.get("bgcolor", self.tr.get("bgcolor", None))
                )
                style = FontFace(fill_color=bgcolor) if bgcolor else None
                colspan = int(self.td_th.get("colspan", "1"))
                rowspan = int(self.td_th.get("rowspan", "1"))
                self.table_row.cell(
                    text="", style=style, colspan=colspan, rowspan=rowspan
                )
            self.td_th = None
        if tag == "font":
            if self.style_stack:
                font_face = self.style_stack.pop()
                self.font_family = font_face.family or self.font_family
                self.font_size_pt = font_face.size_pt or self.font_size_pt
                self.font_emphasis = font_face.emphasis
                self.font_color = font_face.color
        if tag == "sup":
            self.pdf.char_vpos = "LINE"
        if tag == "sub":
            self.pdf.char_vpos = "LINE"
        if tag == "title":
            self._in_title = False

    def feed(self, data):
        super().feed(data)
        while self._tags_stack and self._tags_stack[-1] in self.HTML_UNCLOSED_TAGS:
            self._tags_stack.pop()
        self._end_paragraph()  # render the final chunk of text and clean up our local context.
        if self._tags_stack and self.warn_on_tags_not_matching:
            LOGGER.warning("Missing HTML end tag for <%s>", self._tags_stack[-1])

    def put_link(self, text):
        "Insert a hyperlink"
        prev_style = FontFace(
            family=self.font_family,
            emphasis=self.font_emphasis,
            size_pt=self.font_size_pt,
            color=self.font_color,
        )
        tag_style = self.tag_styles["a"]
        if tag_style.color:
            self.font_color = tag_style.color
        self.font_family = tag_style.family or self.font_family
        self.font_size_pt = tag_style.size_pt or self.font_size_pt
        if tag_style.emphasis:
            self.font_emphasis |= tag_style.emphasis
        self._write_paragraph(text, link=self.href)
        # Restore previous style:
        self.font_family = prev_style.family or self.font_family
        self.font_size_pt = prev_style.size_pt or self.font_size_pt
        self.font_emphasis = prev_style.emphasis
        self.font_color = prev_style.color

    # pylint: disable=no-self-use
    def render_toc(self, pdf, outline):
        "This method can be overridden by subclasses to customize the Table of Contents style."
        pdf.ln()
        for section in outline:
            link = pdf.add_link(page=section.page_number)
            text = f'{" " * section.level * 2} {section.name}'
            text += f' {"." * (60 - section.level*2 - len(section.name))} {section.page_number}'
            pdf.multi_cell(
                w=pdf.epw,
                h=pdf.font_size,
                text=text,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                link=link,
            )

    # Subclasses of _markupbase.ParserBase must implement this:
    def error(self, message):
        raise RuntimeError(message)


def _scale_units(pdf, in_tag_styles):
    conversion_factor = get_scale_factor("mm") / pdf.k
    out_tag_styles = {}
    for tag_name, tag_style in in_tag_styles.items():
        if isinstance(tag_style, TextStyle):
            out_tag_styles[tag_name] = tag_style.replace(
                t_margin=tag_style.t_margin * conversion_factor,
                l_margin=(
                    tag_style.l_margin * conversion_factor
                    if isinstance(tag_style.l_margin, (int, float))
                    else tag_style.l_margin
                ),
                b_margin=tag_style.b_margin * conversion_factor,
            )
        else:
            out_tag_styles[tag_name] = tag_style
    return out_tag_styles


def ul_prefix(ul_type, is_ttf_font):
    if ul_type == "disc":
        return BULLET_UNICODE if is_ttf_font else MESSAGE_WAITING_WIN1252
    if ul_type == "circle":
        return RING_OPERATOR_UNICODE if is_ttf_font else DEGREE_SIGN_WIN1252
    if len(ul_type) == 1:
        return ul_type
    raise NotImplementedError(f"Unsupported type: {ul_type}")


def ol_prefix(ol_type, index):
    if ol_type == "1":
        return index
    if ol_type == "a":
        return ascii_lowercase[index - 1]
    if ol_type == "A":
        return ascii_uppercase[index - 1]
    if ol_type == "I":
        return int2roman(index)
    if ol_type == "i":
        return int2roman(index).lower()
    raise NotImplementedError(f"Unsupported type: {ol_type}")


class HTMLMixin:
    """
    [**DEPRECATED since v2.6.0**]
    You can now directly use the `FPDF.write_html()` method
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            (
                "The HTMLMixin class is deprecated since v2.6.0. "
                "Simply use the FPDF class as a replacement."
            ),
            DeprecationWarning,
            stacklevel=get_stack_level(),
        )
