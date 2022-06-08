"""HTML Renderer for FPDF.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

# Inspired by tuto5.py and several examples from fpdf.org, html2fpdf, etc.

import html
import logging
from html.parser import HTMLParser

from .enums import XPos, YPos


LOGGER = logging.getLogger(__name__)
BULLET_WIN1252 = "\x95"  # BULLET character in Windows-1252 encoding
DEFAULT_HEADING_SIZES = dict(h1=24, h2=18, h3=14, h4=12, h5=10, h6=8)

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
    return int(px) * 25.4 / 72


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
    """Render basic HTML to FPDF"""

    def __init__(
        self,
        pdf,
        image_map=None,
        li_tag_indent=5,
        table_line_separators=False,
        ul_bullet_char=BULLET_WIN1252,
        heading_sizes=None,
        **_,
    ):
        """
        Args:
            pdf (FPDF): an instance of `fpdf.FPDF`
            image_map (function): an optional one-argument function that map <img> "src"
                to new image URLs
            li_tag_indent (int): numeric indentation of <li> elements
            table_line_separators (bool): enable horizontal line separators in <table>
            ul_bullet_char (str): bullet character for <ul> elements
        """
        super().__init__()
        self.pdf = pdf
        self.image_map = image_map or (lambda src: src)
        self.li_tag_indent = li_tag_indent
        self.table_line_separators = table_line_separators
        self.ul_bullet_char = ul_bullet_char
        self.style = dict(b=False, i=False, u=False)
        self.href = ""
        self.align = ""
        self.page_links = {}
        self.font_stack = []
        self.indent = 0
        self.bullet = []
        self.font_size = pdf.font_size_pt
        self.set_font(pdf.font_family or "times", size=self.font_size)
        self.font_color = 0, 0, 0  # initialize font color, r,g,b format
        self.table = None  # table attributes
        self.table_col_width = None  # column (header) widths
        self.table_col_index = None  # current column index
        self.td = None  # inside a <td>, attributes dict
        self.th = None  # inside a <th>, attributes dict
        self.tr = None  # inside a <tr>, attributes dict
        self.thead = None  # inside a <thead>, attributes dict
        self.tfoot = None  # inside a <tfoot>, attributes dict
        self.tr_index = None  # row index
        self.theader = None  # table header cells
        self.tfooter = None  # table footer cells
        self.theader_out = self.tfooter_out = False
        self.table_row_height = 0
        self.heading_level = None
        self.heading_sizes = dict(**DEFAULT_HEADING_SIZES)
        if heading_sizes:
            self.heading_sizes.update(heading_sizes)
        self._only_imgs_in_td = False

    def width2unit(self, length):
        "Handle conversion of % measures into the measurement unit used"
        if length[-1] == "%":
            total = self.pdf.w - self.pdf.r_margin - self.pdf.l_margin
            if self.table["width"][-1] == "%":
                total *= int(self.table["width"][:-1]) / 100
            return int(length[:-1]) * total / 100
        return int(length)

    def handle_data(self, data):
        if self.td is not None:  # drawing a table?
            self._insert_td(data)
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
        else:
            data = data.replace("\n", " ")
            if self.href:
                self.put_link(data)
            else:
                if self.heading_level:
                    self.pdf.start_section(data, self.heading_level - 1)
                LOGGER.debug("write '%s' h=%d", data.replace("\n", "\\n"), self.h)
                self.pdf.write(self.h, data)

    def _insert_td(self, data=""):
        self._only_imgs_in_td = False
        width = self._td_width()
        height = int(self.td.get("height", 0)) // 4 or self.h * 1.30
        if not self.table_row_height:
            self.table_row_height = height
        elif self.table_row_height > height:
            height = self.table_row_height
        border = int(self.table.get("border", 0))
        if self.th:
            self.set_style("B", True)
            border = border or "B"
            align = self.td.get("align", "C")[0].upper()
        else:
            align = self.td.get("align", "L")[0].upper()
            border = border and "LR"
        bgcolor = color_as_decimal(self.td.get("bgcolor", self.tr.get("bgcolor", "")))
        # parsing table header/footer (drawn later):
        if self.thead is not None:
            self.theader.append(
                (
                    dict(
                        w=width,
                        h=height,
                        txt=data,
                        border=border,
                        new_x=XPos.RIGHT,
                        new_y=YPos.TOP,
                        align=align,
                    ),
                    bgcolor,
                )
            )
        if self.tfoot is not None:
            self.tfooter.append(
                (
                    dict(
                        w=width,
                        h=height,
                        txt=data,
                        border=border,
                        new_x=XPos.RIGHT,
                        new_y=YPos.TOP,
                        align=align,
                    ),
                    bgcolor,
                )
            )
        # check if reached end of page, add table footer and header:
        if self.tfooter:
            height += self.tfooter[0][0]["h"]
        if self.pdf.y + height > self.pdf.page_break_trigger and not self.th:
            self.output_table_footer()
            self.pdf.add_page(same=True)
            self.theader_out = self.tfooter_out = False
        if self.tfoot is None and self.thead is None:
            if not self.theader_out:
                self.output_table_header()
            self.box_shadow(width, height, bgcolor)
            # self.pdf.x may have shifted due to <img> inside <td>:
            self.pdf.set_x(self._td_x())
            LOGGER.debug(
                "td cell x=%d width=%d height=%d border=%s align=%s '%s'",
                self.pdf.x,
                width,
                height,
                border,
                align,
                data.replace("\n", "\\n"),
            )
            self.pdf.cell(
                width,
                height,
                data,
                border=border,
                align=align,
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )

    def _td_x(self):
        "Return the current table cell left side horizontal position"
        prev_cells_total_width = sum(
            self.width2unit(width)
            for width in self.table_col_width[: self.table_col_index]
        )
        return self.table_offset + prev_cells_total_width

    def _td_width(self):
        "Return the current table cell width"
        # pylint: disable=raise-missing-from
        if "width" in self.td:
            column_widths = [self.td["width"]]
        elif "colspan" in self.td:
            i = self.table_col_index
            colspan = int(self.td["colspan"])
            column_widths = self.table_col_width[i : i + colspan]
        else:
            try:
                column_widths = [self.table_col_width[self.table_col_index]]
            except IndexError:
                raise ValueError(
                    f"Width not specified for table column {self.table_col_index},"
                    " unable to continue"
                )
        return sum(self.width2unit(width) for width in column_widths)

    def box_shadow(self, w, h, bgcolor):
        LOGGER.debug("box_shadow w=%d h=%d bgcolor=%s", w, h, bgcolor)
        if bgcolor:
            fill_color = self.pdf.fill_color
            self.pdf.set_fill_color(*bgcolor)
            self.pdf.rect(self.pdf.x, self.pdf.y, w, h, "F")
            self.pdf.fill_color = fill_color

    def output_table_header(self):
        if self.theader:
            b = self.style.get("b")
            self.pdf.set_x(self.table_offset)
            self.set_style("b", True)
            for celldict, bgcolor in self.theader:
                self.box_shadow(celldict["w"], celldict["h"], bgcolor)
                self.pdf.cell(**celldict)  # includes the border
            self.set_style("b", b)
            self.pdf.ln(self.theader[0][0]["h"])
            self.pdf.set_x(self.table_offset)
            # self.pdf.set_x(prev_x)
        self.theader_out = True

    def output_table_footer(self):
        if self.tfooter:
            x = self.pdf.x
            self.pdf.set_x(self.table_offset)
            for celldict, bgcolor in self.tfooter:
                self.box_shadow(celldict["w"], celldict["h"], bgcolor)
                self.pdf.cell(**celldict)
            self.pdf.ln(self.tfooter[0][0]["h"])
            self.pdf.set_x(x)
        if self.table.get("border"):
            self.output_table_sep()
        self.tfooter_out = True

    def output_table_sep(self):
        x1 = self.pdf.x
        y1 = self.pdf.y
        width = sum(self.width2unit(length) for length in self.table_col_width)
        self.pdf.line(x1, y1, x1 + width, y1)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        LOGGER.debug("STARTTAG %s %s", tag, attrs)
        if tag in ("b", "i", "u"):
            self.set_style(tag, True)
        if tag == "a":
            self.href = attrs["href"]
        if tag == "br":
            self.pdf.ln(self.h)
        if tag == "p":
            self.pdf.ln(self.h)
            if attrs:
                self.align = attrs.get("align")
        if tag in self.heading_sizes:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.heading_level = int(tag[1:])
            hsize = self.heading_sizes[tag]
            self.pdf.set_text_color(150, 0, 0)
            self.set_font(size=hsize)
            self.pdf.ln(self.h)
            if attrs:
                self.align = attrs.get("align")
        if tag == "hr":
            self.pdf.add_page(same=True)
        if tag == "pre":
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.set_font("courier", 11)
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
            self.table = {k.lower(): v for k, v in attrs.items()}
            if "width" not in self.table:
                self.table["width"] = "100%"
            if self.table["width"][-1] == "%":
                w = self.pdf.w - self.pdf.r_margin - self.pdf.l_margin
                w *= int(self.table["width"][:-1]) / 100
                self.table_offset = (self.pdf.w - w) / 2
            self.table_col_width = []
            self.theader_out = self.tfooter_out = False
            self.theader = []
            self.tfooter = []
            self.thead = None
            self.tfoot = None
            self.pdf.ln()
        if tag == "tr":
            self.tr_index = 0 if self.tr_index is None else (self.tr_index + 1)
            self.tr = {k.lower(): v for k, v in attrs.items()}
            self.table_col_index = 0
            self.table_row_height = 0
            self.pdf.set_x(self.table_offset)
            # Adding an horizontal line separator between rows:
            if self.table_line_separators and self.tr_index > 0:
                self.output_table_sep()
        if tag == "td":
            self.td = {k.lower(): v for k, v in attrs.items()}
            if "width" in self.td and self.table_col_index >= len(self.table_col_width):
                assert self.table_col_index == len(
                    self.table_col_width
                ), f"table_col_index={self.table_col_index} #table_col_width={len(self.table_col_width)}"
                self.table_col_width.append(self.td["width"])
            if attrs:
                self.align = attrs.get("align")
            self._only_imgs_in_td = False
        if tag == "th":
            self.td = {k.lower(): v for k, v in attrs.items()}
            self.th = True
            if "width" in self.td and self.table_col_index >= len(self.table_col_width):
                assert self.table_col_index == len(
                    self.table_col_width
                ), f"table_col_index={self.table_col_index} #table_col_width={len(self.table_col_width)}"
                self.table_col_width.append(self.td["width"])
        if tag == "thead":
            self.thead = {}
        if tag == "tfoot":
            self.tfoot = {}
        if tag == "img" and "src" in attrs:
            width = px2mm(attrs.get("width", 0))
            height = px2mm(attrs.get("height", 0))
            if self.pdf.y + height > self.pdf.page_break_trigger:
                self.pdf.add_page(same=True)
            y = self.pdf.get_y()
            if self.table_col_index is not None:
                self._only_imgs_in_td = True
                # <img> in a <td>: its width must not exceed the cell width:
                td_width = self._td_width()
                if not width or width > td_width:
                    if width:  # Preserving image aspect ratio:
                        height *= td_width / width
                    width = td_width
                x = self._td_x()
                if self.align and self.align[0].upper() == "C":
                    x += (td_width - width) / 2
            else:
                x = self.pdf.get_x()
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
            self.pdf.image(
                self.image_map(attrs["src"]), x, y, width, height, link=self.href
            )
            self.pdf.set_x(x + width)
            if self.table_col_index is not None:
                # <img> in a <td>: we grow the cell height according to the image height:
                if height > self.table_row_height:
                    self.table_row_height = height
            else:
                self.pdf.set_y(y + height)
        if tag in ("b", "i", "u"):
            self.set_style(tag, True)
        if tag == "center":
            self.align = "Center"
        if tag == "toc":
            self.pdf.insert_toc_placeholder(
                self.render_toc, pages=int(attrs.get("pages", 1))
            )

    def handle_endtag(self, tag):
        # Closing tag
        LOGGER.debug("ENDTAG %s", tag)
        if tag in self.heading_sizes:
            self.heading_level = None
            face, size, color = self.font_stack.pop()
            self.set_font(face, size)
            self.set_text_color(*color)
            self.pdf.ln(self.h)
            self.align = None
        if tag == "pre":
            face, size, color = self.font_stack.pop()
            self.set_font(face, size)
            self.set_text_color(*color)
        if tag == "blockquote":
            self.set_text_color(*self.font_color)
            self.indent -= 1
            self.pdf.ln(3)
        if tag == "strong":
            tag = "b"
        if tag == "em":
            tag = "i"
        if tag in ("b", "i", "u"):
            self.set_style(tag, False)
        if tag == "a":
            self.href = ""
        if tag == "p":
            self.pdf.ln(self.h)
            self.align = ""
        if tag in ("ul", "ol"):
            self.indent -= 1
            self.bullet.pop()
        if tag == "table":
            if not self.tfooter_out:
                self.output_table_footer()
            self.table = None
            self.th = False
            self.theader = None
            self.tfooter = None
            self.pdf.ln(self.h)
            self.tr_index = None
        if tag == "thead":
            self.thead = None
            self.tr_index = None
        if tag == "tfoot":
            self.tfoot = None
            self.tr_index = None
        if tag == "tbody":
            self.tbody = None
            self.tr_index = None
        if tag == "tr":
            if self.tfoot is None:
                self.pdf.ln(self.table_row_height)
            self.table_col_index = None
            self.tr = None
        if tag in ("td", "th"):
            if self.th:
                LOGGER.debug("revert style")
                self.set_style("b", False)  # revert style
            elif self._only_imgs_in_td:
                self._insert_td()
            self.table_col_index += int(self.td.get("colspan", "1"))
            self.td = None
            self.th = False
        if tag == "font":
            # recover last font state
            face, size, color = self.font_stack.pop()
            self.font_color = color
            self.set_font(face, size)
            self.set_text_color(*self.font_color)
        if tag == "center":
            self.align = None

    def set_font(self, face=None, size=None):
        if face:
            self.font_face = face
        if size:
            self.font_size = size
            self.h = size / 72 * 25.4
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

    def render_toc(self, pdf, outline):
        "This method can be overriden by subclasses to customize the Table of Contents style."
        pdf.ln()
        for section in outline:
            link = pdf.add_link()
            pdf.set_link(link, page=section.page_number)
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


class HTMLMixin:
    HTML2FPDF_CLASS = HTML2FPDF

    def write_html(self, text, *args, **kwargs):
        """Parse HTML and convert it to PDF"""
        kwargs2 = vars(self)
        # Method arguments must override class & instance attributes:
        kwargs2.update(kwargs)
        h2p = self.HTML2FPDF_CLASS(self, *args, **kwargs2)
        text = html.unescape(text)  # To deal with HTML entities
        h2p.feed(text)
