"""HTML Renderer for FPDF.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

# Inspired by tuto5.py and several examples from fpdf.org, html2fpdf, etc.

import html
import logging
from html.parser import HTMLParser

LOGGER = logging.getLogger(__name__)
BULLET_WIN1252 = "\x95"  # BULLET character in Windows-1252 encoding


def px2mm(px):
    return int(px) * 25.4 / 72


def hex2dec(color="#000000"):
    if not color:
        return None
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
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
        self.font_face = None  # must be initialized before calling HTML.set_font:
        self.set_font(size=self.font_size)
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
        self.hsize = dict(h1=2, h2=1.5, h3=1.17, h4=1, h5=0.83, h6=0.67)

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
            width = self._td_width()
            height = int(self.td.get("height", 0)) // 4 or self.h * 1.30
            if not self.table_row_height and height:
                self.table_row_height = height
            border = int(self.table.get("border", 0))
            if not self.th:
                align = self.td.get("align", "L")[0].upper()
                border = border and "LR"
            else:
                self.set_style("B", True)
                border = border or "B"
                align = self.td.get("align", "C")[0].upper()
            bgcolor = hex2dec(self.td.get("bgcolor", self.tr.get("bgcolor", "")))
            # parsing table header/footer (drawn later):
            if self.thead is not None:
                self.theader.append(((width, height, data, border, 0, align), bgcolor))
            if self.tfoot is not None:
                self.tfooter.append(((width, height, data, border, 0, align), bgcolor))
            # check if reached end of page, add table footer and header:
            if self.tfooter:
                height += self.tfooter[0][0][1]
            if self.pdf.y + height > self.pdf.page_break_trigger and not self.th:
                self.output_table_footer()
                self.pdf.add_page(same=True)
                self.theader_out = self.tfooter_out = False
            if self.tfoot is None and self.thead is None:
                if not self.theader_out:
                    self.output_table_header()
                self.box_shadow(width, self.table_row_height, bgcolor)
                self.pdf.set_x(
                    self._td_x()
                )  # self.pdf.x may have shifted due to <img> inside <td>
                LOGGER.debug(
                    "td cell x=%d width=%d '%s'",
                    self.pdf.x,
                    width,
                    data.replace("\n", "\\n"),
                )
                self.pdf.cell(
                    width, self.table_row_height, data, border=border, ln=0, align=align
                )
        elif self.table is not None:
            # ignore anything else than td inside a table
            pass
        elif self.align:
            LOGGER.debug("cell '%s'", data.replace("\n", "\\n"))
            self.pdf.cell(
                0,
                self.h,
                data,
                border=0,
                ln=1,
                align=self.align[0].upper(),
                link=self.href,
            )
        else:
            data = data.replace("\n", " ")
            if self.href:
                self.put_link(self.href, data)
            else:
                LOGGER.debug("write '%s'", data.replace("\n", "\\n"))
                self.pdf.write(self.h, data)

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
            for cell, bgcolor in self.theader:
                self.box_shadow(cell[0], cell[1], bgcolor)
                self.pdf.cell(*cell)  # includes the border
            self.set_style("b", b)
            self.pdf.ln(self.theader[0][0][1])
            self.pdf.set_x(self.table_offset)
            # self.pdf.set_x(prev_x)
        self.theader_out = True

    def output_table_footer(self):
        if self.tfooter:
            x = self.pdf.x
            self.pdf.set_x(self.table_offset)
            for cell, bgcolor in self.tfooter:
                self.box_shadow(cell[0], cell[1], bgcolor)
                self.pdf.cell(*cell)
            self.pdf.ln(self.tfooter[0][0][1])
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
        if tag in self.hsize:
            k = self.hsize[tag]
            self.pdf.ln(5 * k)
            self.pdf.set_text_color(150, 0, 0)
            self.pdf.set_font_size(12 * k)
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
            self.set_text_color()
        if tag == "font":
            # save previous font state:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            if "color" in attrs:
                color = hex2dec(attrs["color"])
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
            self.set_text_color()
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
            self.table_row_height = 0
            self.pdf.ln()
        if tag == "tr":
            self.tr_index = 0 if self.tr_index is None else (self.tr_index + 1)
            self.tr = {k.lower(): v for k, v in attrs.items()}
            self.table_col_index = 0
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
        if tag == "th":
            self.td = {k.lower(): v for k, v in attrs.items()}
            self.th = True
            if "width" in self.td:
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
                # <img> in a <td>: its width must not exceed the cell width:
                td_width = self._td_width()
                if not width or width > td_width:
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

    def handle_endtag(self, tag):
        # Closing tag
        LOGGER.debug("ENDTAG %s", tag)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.pdf.ln(self.h)
            self.set_font()
            self.set_text_color()
            self.align = None
        if tag == "pre":
            # recover last font state, color is ignored as pre doesn't change it
            face, size, color = self.font_stack.pop()
            self.set_font(face, size)
        if tag == "blockquote":
            self.set_text_color()
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
            self.table_col_index += int(self.td.get("colspan", "1"))
            self.td = None
            self.th = False
        if tag == "font":
            # recover last font state
            face, size, color = self.font_stack.pop()
            self.font_color = color
            self.set_font(face, size)
            self.set_text_color()
        if tag == "center":
            self.align = None

    def set_font(self, face=None, size=None):
        if face:
            self.font_face = face
        if not self.font_face:
            self.font_face = self.pdf.current_font.get("fontkey")
        if size:
            self.font_size = size
            self.h = size / 72 * 25.4
            LOGGER.debug("H %s", self.h)
        style = "".join(s for s in ("b", "i", "u") if self.style.get(s))
        self.pdf.set_font(self.font_face or "times", style, self.font_size or 12)
        self.pdf.set_font_size(self.font_size or 12)

    def set_style(self, tag=None, enable=False):
        # Modify style and select corresponding font
        if tag:
            self.style[tag.lower()] = enable
        style = "".join(s for s in ("b", "i", "u") if self.style.get(s))
        LOGGER.debug("SET_FONT_STYLE %s", style)
        self.pdf.set_font(style=style)

    def set_text_color(self, r=None, g=0, b=0):
        if r is None:
            self.pdf.set_text_color(*self.font_color)
        else:
            self.pdf.set_text_color(r, g, b)

    def put_link(self, url, txt):
        # Put a hyperlink
        self.set_text_color(0, 0, 255)
        self.set_style("u", True)
        self.pdf.write(self.h, txt, url)
        self.set_style("u", False)
        self.set_text_color()

    # Subclasses of _markupbase.ParserBase must implement this:
    def error(self, message):
        raise RuntimeError(message)


class HTMLMixin:
    def write_html(self, text, *args, **kwargs):
        """Parse HTML and convert it to PDF"""
        kwargs2 = vars(self)
        # Method arguments must override class & instance attributes:
        kwargs2.update(kwargs)
        h2p = HTML2FPDF(self, *args, **kwargs2)
        text = html.unescape(text)  # To deal with HTML entities
        h2p.feed(text)
