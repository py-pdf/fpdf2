"""PDF Template Helper for FPDF.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

import csv
import locale
import warnings

from .errors import FPDFException
from .fpdf import FPDF


def rgb(col):
    return (col // 65536), (col // 256 % 256), (col % 256)


def rgb_as_str(col):
    r, g, b = rgb(col)
    if (r == 0 and g == 0 and b == 0) or g == -1:
        return f"{r / 255:.3f} g"
    return f"{r / 255:.3f} {g / 255:.3f} {b / 255:.3f} rg"


class FlexTemplate:
    def __init__(self, pdf, elements=None):
        if elements:
            self.load_elements(elements)
        self.pdf = pdf
        self.handlers = {
            "T": self.text,
            "L": self.line,
            "I": self.image,
            "B": self.rect,
            "BC": self.barcode,
            "C39": self.code39,
            "W": self.write,
        }
        self.texts = {}

    def load_elements(self, elements):
        """Initialize the internal element structures"""
        self.elements = elements
        self.keys = []
        for e in elements:
            if not "priority" in e:
                e["priority"] = 0
            self.keys.append(e["name"].lower())
        #self.keys = [v["name"].lower() for v in self.elements]

    @staticmethod
    def _parse_colorcode(s):
        """Allow hex and oct values for colors"""
        if s[:2] in ["0x", "0X"]:
            return int(s, 16)
        if s[:2] in ["0o", "0O"]:
            return int(s, 8)
        return int(s)

    @staticmethod
    def _parse_multiline(s):
        i = int(s)
        if i > 0:
            return True
        if i < 0:
            return False

    def parse_csv(self, infile, delimiter=",", decimal_sep=".", encoding=None):
        """Parse template format csv file and create elements dict"""

        def varsep_float(s, default="0"):
            """Convert to float with given decimal seperator"""
            # glad to have nonlocal scoping...
            return float((s.strip() or default).replace(decimal_sep, "."))

        handlers = (
            ("name", str),
            ("type", str),
            ("x1", varsep_float),
            ("y1", varsep_float),
            ("x2", varsep_float),
            ("y2", varsep_float),
            ("font", str, "helvetica"),
            ("size", varsep_float, 10.0),
            ("bold", int, 0),
            ("italic", int, 0),
            ("underline", int, 0),
            ("foreground", self._parse_colorcode, 0x0),
            ("background", self._parse_colorcode, 0xFFFFFF),
            ("align", str, "L"),
            ("text", str, ""),
            ("priority", int, 0),
            ("multiline", self._parse_multiline, None),
            ("rotate", varsep_float, 0.0),
        )
        self.elements = []
        if encoding is None:
            encoding = locale.getpreferredencoding()
        hlen = len(handlers)
        with open(infile, encoding=encoding) as f:
            for row in csv.reader(f, delimiter=delimiter):
                rlen = len(row)
                # fill in any missing items
                row[rlen + 1 :] = [""] * (hlen - rlen)
                kargs = {}
                for i, v in enumerate(row):
                    handler = handlers[i]
                    vs = v.strip()
                    if not vs:
                        if len(handler) < 3:
                            raise FPDFException(
                                "Mandatory value '%s' missing in csv data" % handler[0]
                            )
                        kargs[handler[0]] = handler[2]  # default
                    else:
                        kargs[handler[0]] = handler[1](v)
                self.elements.append(kargs)
        self.keys = [v["name"].lower() for v in self.elements]

    def __setitem__(self, name, value):
        if name.lower() not in self.keys:
            raise FPDFException(f"Element not loaded, cannot set item: {name}")
        self.texts[name.lower()] = value

    # setitem shortcut (may be further extended)
    set = __setitem__

    def __contains__(self, name):
        return name.lower() in self.keys

    def __getitem__(self, name):
        if name not in self.keys:
            return None
        key = name.lower()
        if key in self.texts:
            # text for this page:
            return self.texts[key]
        # find first element for default text:
        return next(
            (x["text"] for x in self.elements if x["name"].lower() == key), None
        )

    def split_multicell(self, text, element_name):
        """Divide (\n) a string using a given element width"""
        element = next(
            element
            for element in self.elements
            if element["name"].lower() == element_name.lower()
        )
        style = ""
        if element["bold"]:
            style += "B"
        if element["italic"]:
            style += "I"
        if element["underline"]:
            style += "U"
        self.pdf.set_font(element["font"], style, element["size"])
        return self.pdf.multi_cell(
            w=element["x2"] - element["x1"],
            h=element["y2"] - element["y1"],
            txt=str(text),
            align=element["align"],
            split_only=True,
        )

    @staticmethod
    def text(
        pdf,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        bold=False,
        italic=False,
        underline=False,
        align="",
        foreground=0,
        background=0xFFFFFF,
        multiline=None,
        **__,
    ):
        if not text:
            return
        if pdf.text_color != rgb_as_str(foreground):
            pdf.set_text_color(*rgb(foreground))
        if pdf.fill_color != rgb_as_str(background):
            pdf.set_fill_color(*rgb(background))

        font = font.strip().lower()
        style = ""
        for tag in "B", "I", "U":
            if text.startswith(f"<{tag}>") and text.endswith(f"</{tag}>"):
                text = text[3:-4]
                style += tag
        if bold:
            style += "B"
        if italic:
            style += "I"
        if underline:
            style += "U"
        pdf.set_font(font, style, size)
        pdf.set_xy(x1, y1)
        width, height = x2 - x1, y2 - y1
        if multiline is None:  # write without wrapping/trimming (default)
            pdf.cell(
                w=width, h=height, txt=text, border=0, ln=0, align=align, fill=True
            )
        elif multiline:  # automatic word - warp
            pdf.multi_cell(
                w=width, h=height, txt=text, border=0, align=align, fill=True
            )
        else:  # trim to fit exactly the space defined
            text = pdf.multi_cell(
                w=width, h=height, txt=text, align=align, split_only=True
            )[0]
            pdf.cell(
                w=width, h=height, txt=text, border=0, ln=0, align=align, fill=True
            )

    @staticmethod
    def line(pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, foreground=0, background=0xFFFFFF, **__):
        if pdf.draw_color.lower() != rgb_as_str(foreground):
            pdf.set_draw_color(*rgb(foreground))
        if pdf.fill_color != rgb_as_str(background):
            pdf.set_fill_color(*rgb(background))
        pdf.set_line_width(size)
        pdf.line(x1, y1, x2, y2)

    @staticmethod
    def rect(pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, foreground=0, background=0xFFFFFF, **__):
        if pdf.draw_color.lower() != rgb_as_str(foreground):
            pdf.set_draw_color(*rgb(foreground))
        if pdf.fill_color != rgb_as_str(background):
            pdf.set_fill_color(*rgb(background))
        pdf.set_line_width(size)
        pdf.rect(x1, y1, x2 - x1, y2 - y1, style="FD")

    @staticmethod
    def image(pdf, *_, x1=0, y1=0, x2=0, y2=0, text="", **__):
        if text:
            pdf.image(text, x1, y1, w=x2 - x1, h=y2 - y1, link="")

    @staticmethod
    def barcode(
        pdf,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=1,
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        if pdf.draw_color.lower() != rgb_as_str(foreground):
            pdf.set_draw_color(*rgb(foreground))
        font = font.lower().strip()
        if font == "interleaved 2of5 nt":
            pdf.interleaved2of5(text, x1, y1, w=size, h=y2 - y1)

    @staticmethod
    def code39(
        pdf,
        text,
        x,
        y,
        *_,
        w=1.5,
        h=5,
        **__,
    ):
        pdf.code39(text, x, y, w, h)

    # Added by Derek Schwalenberg Schwalenberg1013@gmail.com to allow (url) links in
    # templates (using write method) 2014-02-22
    @staticmethod
    def write(
        pdf,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        bold=False,
        italic=False,
        underline=False,
        link="",
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        if pdf.text_color != rgb_as_str(foreground):
            pdf.set_text_color(*rgb(foreground))
        font = font.strip().lower()
        style = ""
        for tag in "B", "I", "U":
            if text.startswith(f"<{tag}>") and text.endswith(f"</{tag}>"):
                text = text[3:-4]
                style += tag
        if bold:
            style += "B"
        if italic:
            style += "I"
        if underline:
            style += "U"
        pdf.set_font(font, style, size)
        pdf.set_xy(x1, y1)
        pdf.write(5, text, link)

    def _render_element(self, element):
        handler_name = element["type"].upper()
        if element.get("rotate"):
            with self.pdf.rotation(element["rotate"], element["x1"], element["y1"]):
                self.handlers[handler_name](self.pdf, **element)
        else:
            self.handlers[handler_name](self.pdf, **element)

    def render(self, offsetx=0.0, offsety=0.0, rotate=0.0):
        sorted_elements = sorted(self.elements, key=lambda x: x["priority"])
        for element in sorted_elements:
            element = element.copy()
            element["text"] = self.texts.get(element["name"].lower(), element.get("text", ""))
            element["x1"] = element["x1"] + offsetx
            element["y1"] = element["y1"] + offsety
            element["x2"] = element["x2"] + offsetx
            element["y2"] = element["y2"] + offsety
            if rotate:  # don't rotate by 0.0 degrees
                with self.pdf.rotation(rotate, offsetx, offsety):
                    self._render_element(element)
            else:
                self._render_element(element)

        self.texts = {}  # reset modified entries for the next page


class Template(FlexTemplate):
    # Disabling this check due to the "format" parameter below:
    # pylint: disable=redefined-builtin
    def __init__(
        self,
        infile=None,
        elements=None,
        format="A4",
        orientation="portrait",
        unit="mm",
        title="",
        author="",
        subject="",
        creator="",
        keywords="",
    ):
        """
        Args:
            infile (str): [**DEPRECATED**] unused, will be removed in a later version
        """
        pdf = FPDF(format=format, orientation=orientation, unit=unit)
        pdf.set_title(title)
        pdf.set_author(author)
        pdf.set_creator(creator)
        pdf.set_subject(subject)
        pdf.set_keywords(keywords)
        super().__init__(pdf=pdf, elements=elements)

    def add_page(self):
        if self.pdf.page:
            self.render()
        self.pdf.add_page()

    def render(self, outfile=None, dest=None):
        """
        Args:
            outfile (str): optional output PDF file path. If ommited, the
                `.pdf.output(...)` method can be manuallyy called afterwise.
            dest (str): [**DEPRECATED**] unused, will be removed in a later version
        """
        if dest:
            warnings.warn(
                '"dest" is unused and will soon be deprecated',
                PendingDeprecationWarning,
            )
        self.pdf.set_font("helvetica", "B", 16)
        self.pdf.set_auto_page_break(False, margin=0)
        super().render()
        if outfile:
            pdf.output(outfile)
