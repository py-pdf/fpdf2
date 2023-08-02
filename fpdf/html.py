"HTML renderer"

import logging, warnings
from html.parser import HTMLParser

from .enums import TextEmphasis, XPos, YPos
from .errors import FPDFException
from .deprecation import get_stack_level
from .fonts import FontFace
from .table import Table, TableBordersLayout

import re

LOGGER = logging.getLogger(__name__)
BULLET_WIN1252 = "\x95"  # BULLET character in Windows-1252 encoding
DEFAULT_HEADING_SIZES = dict(h1=24, h2=18, h3=14, h4=12, h5=10, h6=8)
LEADING_SPACE = re.compile(r"^\s+")
WHITESPACE = re.compile(r"(\s)(\s*)")
TRAILING_SPACE = re.compile(r"\s$")

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


def px2mm(px):
    return px * 25.4 / 72


def color_as_decimal(color="#000000"):
    if not color:
        return None

    # Checks if color is a name and gets the hex value
    hexcolor = COLOR_DICT.get(color.lower(), color)

    if len(hexcolor) == 4:
        r = int(hexcolor[1] * 2, 16)
        g = int(hexcolor[2] * 2, 16)
        b = int(hexcolor[3] * 2, 16)
        return r, g, b

    r = int(hexcolor[1:3], 16)
    g = int(hexcolor[3:5], 16)
    b = int(hexcolor[5:7], 16)
    return r, g, b


class HTML2FPDF(HTMLParser):
    "Render basic HTML to FPDF"

    HTML_UNCLOSED_TAGS = ("br", "dd", "dt", "hr", "img", "li", "td", "tr")

    def __init__(
        self,
        pdf,
        image_map=None,
        li_tag_indent=5,
        dd_tag_indent=10,
        table_line_separators=False,
        ul_bullet_char=BULLET_WIN1252,
        heading_sizes=None,
        pre_code_font="courier",
        warn_on_tags_not_matching=True,
        **_,
    ):
        """
        Args:
            pdf (FPDF): an instance of `fpdf.FPDF`
            image_map (function): an optional one-argument function that map <img> "src"
                to new image URLs
            li_tag_indent (int): numeric indentation of <li> elements
            dd_tag_indent (int): numeric indentation of <dd> elements
            table_line_separators (bool): enable horizontal line separators in <table>
            ul_bullet_char (str): bullet character for <ul> elements
            heading_sizes (dict): font size per heading level names ("h1", "h2"...)
            pre_code_font (str): font to use for <pre> & <code> blocks
            warn_on_tags_not_matching (bool): control warnings production for unmatched HTML tags
        """
        super().__init__()
        self.pdf = pdf
        self.image_map = image_map or (lambda src: src)
        self.li_tag_indent = li_tag_indent
        self.dd_tag_indent = dd_tag_indent
        self.ul_bullet_char = ul_bullet_char
        self.style = dict(b=False, i=False, u=False)
        self.pre_formatted = False
        self.follows_fmt_tag = False
        self.follows_trailing_space = False
        self.href = ""
        self.align = ""
        self.page_links = {}
        self.font_stack = []
        self.indent = 0
        self.bullet = []
        self.font_size = pdf.font_size_pt
        self.set_font(pdf.font_family or "times", size=self.font_size)
        self.font_color = tuple((255 * v for v in pdf.text_color.colors))
        self.heading_level = None
        self.heading_sizes = dict(**DEFAULT_HEADING_SIZES)
        self.heading_above = 0.2  # extra space above heading, relative to font size
        self.heading_below = 0.2  # extra space below heading, relative to font size
        if heading_sizes:
            self.heading_sizes.update(heading_sizes)
        self.pre_code_font = pre_code_font
        self.warn_on_tags_not_matching = warn_on_tags_not_matching
        self._tags_stack = []
        # <table>-related properties:
        self.table_line_separators = table_line_separators
        self.table = None  # becomes a Table instance when processing <table> tags
        self.table_row = None  # becomes a Row instance when processing <tr> tags
        self.tr = None  # becomes a dict of attributes when processing <tr> tags
        self.td_th = None  # becomes a dict of attributes when processing <td>/<th> tags
        # "inserted" is a special attribute indicating that a cell has be inserted in self.table_row

    def handle_data(self, data):
        trailing_space_flag = TRAILING_SPACE.search(data)
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
            emphasis = 0
            if self.td_th.get("b"):
                emphasis |= TextEmphasis.B
            if self.td_th.get("i"):
                emphasis |= TextEmphasis.I
            if self.td_th.get("U"):
                emphasis |= TextEmphasis.U
            style = None
            if bgcolor or emphasis:
                style = FontFace(emphasis=emphasis, fill_color=bgcolor)
            self.table_row.cell(text=data, align=align, style=style, colspan=colspan)
            self.td_th["inserted"] = True
        elif self.table is not None:
            # ignore anything else than td inside a table
            pass
        elif self.align:
            LOGGER.debug("align '%s'", data.replace("\n", "\\n"))
            self.pdf.multi_cell(
                0,
                self.h,
                data,
                border=0,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                align=self.align[0].upper(),
                link=self.href,
            )
        elif self.pre_formatted:  # for pre blocks
            self.pdf.write(self.h, data)

        elif self.follows_fmt_tag and not self.follows_trailing_space:
            # don't trim leading whitespace if following a format tag with no trailing whitespace
            data = WHITESPACE.sub(whitespace_repl, data)
            if trailing_space_flag:
                self.follows_trailing_space = True
            if self.href:
                self.put_link(data)
            else:
                if self.heading_level:
                    self.pdf.start_section(data, self.heading_level - 1, strict=False)
                LOGGER.debug(
                    "write '%s' h=%d",
                    WHITESPACE.sub(whitespace_repl, data),
                    self.h,
                )
                self.pdf.write(self.h, data)
            self.follows_fmt_tag = False

        else:
            data = LEADING_SPACE.sub(leading_whitespace_repl, data)
            data = WHITESPACE.sub(whitespace_repl, data)
            self.follows_trailing_space = trailing_space_flag
            if self.href:
                self.put_link(data)
            else:
                if self.heading_level:
                    self.pdf.start_section(data, self.heading_level - 1, strict=False)
                LOGGER.debug(
                    "write '%s' h=%d",
                    WHITESPACE.sub(whitespace_repl, data),
                    self.h,
                )
                self.pdf.write(self.h, data)
            self.follows_fmt_tag = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        LOGGER.debug("STARTTAG %s %s", tag, attrs)
        self._tags_stack.append(tag)
        if tag == "dt":
            self.pdf.ln(self.h)
            tag = "b"
        if tag == "dd":
            self.pdf.ln(self.h)
            self.pdf.write(self.h, " " * self.dd_tag_indent)
        if tag == "strong":
            tag = "b"
        if tag == "em":
            tag = "i"
        if tag in ("b", "i", "u"):
            if self.td_th is not None:
                self.td_th[tag] = True
            else:
                self.set_style(tag, True)
        if tag == "a":
            self.href = attrs["href"]
        if tag == "br":
            self.pdf.ln(self.h)
        if tag == "p":
            self.pdf.ln(self.h)
            if "align" in attrs:
                self.align = attrs.get("align")
            if "line-height" in attrs:
                line_height = float(attrs.get("line-height"))
                self.h = px2mm(self.font_size) * line_height
        if tag in self.heading_sizes:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.heading_level = int(tag[1:])
            hsize = self.heading_sizes[tag]
            self.pdf.set_text_color(150, 0, 0)
            self.pdf.ln(self.h + self.heading_above * hsize)  # more space above heading
            self.set_font(size=hsize)
            if attrs:
                self.align = attrs.get("align")
        if tag == "hr":
            self.pdf.add_page(same=True)
        if tag == "code":
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.set_font(self.pre_code_font, 11)
        if tag == "pre":
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.set_font(self.pre_code_font, 11)
            self.pre_formatted = True
        if tag == "blockquote":
            self.pdf.set_text_color(100, 0, 45)
            self.indent += 1
            self.pdf.ln(3)
        if tag == "ul":
            self.indent += 1
            self.bullet.append(self.ul_bullet_char)
        if tag == "ol":
            self.indent += 1
            self.bullet.append(0)
        if tag == "li":
            self.pdf.ln(self.h + 2)
            self.pdf.set_text_color(190, 0, 0)
            bullet = self.bullet[self.indent - 1]
            if not isinstance(bullet, str):
                bullet += 1
                self.bullet[self.indent - 1] = bullet
                bullet = f"{bullet}. "
            self.pdf.write(self.h, f"{' ' * self.li_tag_indent * self.indent}{bullet} ")
            self.set_text_color(*self.font_color)
        if tag == "font":
            # save previous font state:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            if "color" in attrs:
                color = color_as_decimal(attrs["color"])
                self.font_color = color
            if "face" in attrs:
                face = attrs.get("face").lower()
                try:
                    self.pdf.set_font(face)
                    self.font_face = face
                except RuntimeError:
                    pass  # font not found, ignore
            if "size" in attrs:
                self.font_size = int(attrs.get("size"))
            self.set_font()
            self.set_text_color(*self.font_color)
        if tag == "table":
            width = attrs.get("width")
            if width:
                if width[-1] == "%":
                    width = self.pdf.epw * int(width[:-1]) / 100
                else:
                    width = px2mm(int(width))
            if "border" in attrs:
                borders_layout = (
                    "ALL" if self.table_line_separators else "NO_HORIZONTAL_LINES"
                )
            else:
                borders_layout = (
                    "HORIZONTAL_LINES"
                    if self.table_line_separators
                    else "SINGLE_TOP_LINE"
                )
            align = attrs.get("align", "center").upper()
            self.table = Table(
                self.pdf,
                align=align,
                borders_layout=borders_layout,
                line_height=self.h * 1.30,
                width=width,
            )
            self.pdf.ln()
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
                self.td_th["align"] = "CENTER"
                self.td_th["b"] = True
            elif len(self.table.rows) == 1 and not self.table_row.cells:
                # => we are in the 1st <tr>, and the 1st cell is a <td>
                # => we do not treat the first row as a header
                # pylint: disable=protected-access
                self.table._borders_layout = TableBordersLayout.NONE
                self.table._first_row_as_headings = False
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
            width = px2mm(int(attrs.get("width", 0)))
            height = px2mm(int(attrs.get("height", 0)))
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
            if self.pdf.y + height > self.pdf.page_break_trigger:
                self.pdf.add_page(same=True)
            x, y = self.pdf.get_x(), self.pdf.get_y()
            if self.align and self.align[0].upper() == "C":
                x = self.pdf.w / 2 - width / 2
            LOGGER.debug(
                'image "%s" x=%d y=%d width=%d height=%d',
                attrs["src"],
                x,
                y,
                width,
                height,
            )
            info = self.pdf.image(
                self.image_map(attrs["src"]), x, y, width, height, link=self.href
            )
            self.pdf.set_y(y + info.rendered_height)
        if tag == "center":
            self.align = "Center"
        if tag == "toc":
            self.pdf.insert_toc_placeholder(
                self.render_toc, pages=int(attrs.get("pages", 1))
            )
        if tag == "sup":
            self.pdf.char_vpos = "SUP"
        if tag == "sub":
            self.pdf.char_vpos = "SUB"

    def handle_endtag(self, tag):
        LOGGER.debug("ENDTAG %s", tag)
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
        if tag in self.heading_sizes:
            self.heading_level = None
            face, size, color = self.font_stack.pop()
            # more space below heading:
            self.pdf.ln(self.h + self.h * self.heading_below)
            self.set_font(face, size)
            self.set_text_color(*color)
            self.align = None
        if tag == "code":
            face, size, color = self.font_stack.pop()
            self.set_font(face, size)
            self.set_text_color(*color)
        if tag == "pre":
            face, size, color = self.font_stack.pop()
            self.set_font(face, size)
            self.set_text_color(*color)
            self.pre_formatted = False
        if tag == "blockquote":
            self.set_text_color(*self.font_color)
            self.indent -= 1
            self.pdf.ln(3)
        if tag in ("strong", "dt"):
            tag = "b"
        if tag == "em":
            tag = "i"
        if tag in ("b", "i", "u"):
            if not self.td_th is not None:
                self.set_style(tag, False)
            self.follows_fmt_tag = True
        if tag == "a":
            self.href = ""
        if tag == "p":
            self.pdf.ln(self.h)
            self.align = ""
            self.h = px2mm(self.font_size)
        if tag in ("ul", "ol"):
            self.indent -= 1
            self.bullet.pop()
        if tag == "table":
            self.table.render()
            self.table = None
            self.pdf.ln(self.h)
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
                self.table_row.cell(text="", style=style)
            self.td_th = None
        if tag == "font":
            # recover last font state
            face, size, color = self.font_stack.pop()
            self.font_color = color
            self.set_font(face, size)
            self.set_text_color(*self.font_color)
        if tag == "center":
            self.align = None
        if tag == "sup":
            self.pdf.char_vpos = "LINE"
            self.follows_fmt_tag = True
        if tag == "sub":
            self.pdf.char_vpos = "LINE"
            self.follows_fmt_tag = True

    def feed(self, data):
        super().feed(data)
        while self._tags_stack and self._tags_stack[-1] in self.HTML_UNCLOSED_TAGS:
            self._tags_stack.pop()
        if self._tags_stack and self.warn_on_tags_not_matching:
            LOGGER.warning("Missing HTML end tag for <%s>", self._tags_stack[-1])

    def set_font(self, face=None, size=None):
        if face:
            self.font_face = face
        if size:
            self.font_size = size
            self.h = px2mm(size)
            LOGGER.debug("H %s", self.h)
        style = "".join(s for s in ("b", "i", "u") if self.style.get(s)).upper()
        if (self.font_face, style) != (self.pdf.font_family, self.pdf.font_style):
            self.pdf.set_font(self.font_face, style, self.font_size)
        if self.font_size != self.pdf.font_size:
            self.pdf.set_font_size(self.font_size)

    def set_style(self, tag=None, enable=False):
        # Modify style and select corresponding font
        if tag:
            self.style[tag.lower()] = enable
        style = "".join(s for s in ("b", "i", "u") if self.style.get(s))
        LOGGER.debug("SET_FONT_STYLE %s", style)
        self.pdf.set_font(style=style)

    def set_text_color(self, r=None, g=0, b=0):
        self.pdf.set_text_color(r, g, b)

    def put_link(self, txt):
        # Put a hyperlink
        self.set_text_color(0, 0, 255)
        self.set_style("u", True)
        self.pdf.write(self.h, txt, self.href)
        self.set_style("u", False)
        self.set_text_color(*self.font_color)

    # pylint: disable=no-self-use
    def render_toc(self, pdf, outline):
        "This method can be overriden by subclasses to customize the Table of Contents style."
        pdf.ln()
        for section in outline:
            link = pdf.add_link(page=section.page_number)
            text = f'{" " * section.level * 2} {section.name}'
            text += f' {"." * (60 - section.level*2 - len(section.name))} {section.page_number}'
            pdf.multi_cell(
                w=pdf.epw,
                h=pdf.font_size,
                txt=text,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                link=link,
            )

    # Subclasses of _markupbase.ParserBase must implement this:
    def error(self, message):
        raise RuntimeError(message)


def leading_whitespace_repl(matchobj):
    trimmed_str = ""
    for char in matchobj.group(0):  # check if leading whitespace contains nbsp
        if char == "\u00a0":
            trimmed_str += "\u00a0"
        elif char == "\u202f":
            trimmed_str += "\u202f"
    return trimmed_str


def whitespace_repl(matchobj):
    trimmed_str = ""
    for char in matchobj.group(
        1
    ):  # allow 1 whitespace char, check for narrow no-break space
        if char == "\u202f":
            trimmed_str += "\u202f"
        else:
            trimmed_str += " "
    for char in matchobj.group(2):  # remove following whitespace char unless nbsp
        if char == "\u00a0":
            trimmed_str += "\u00a0"
        elif char == "\u202f":
            trimmed_str += "\u202f"
    return trimmed_str


class HTMLMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            # pylint: disable=implicit-str-concat
            "The HTMLMixin class is deprecated. "
            "Simply use the FPDF class as a replacement.",
            DeprecationWarning,
            stacklevel=get_stack_level(),
        )
