"""PDF Template Helper for FPDF.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

import csv
import warnings

from .errors import FPDFException
from .fpdf import FPDF
from .util import try_to_type


def rgb(col):
    return (col // 65536), (col // 256 % 256), (col % 256)


class Template:
    # Disabling this check due to the "format" parameter below:
    # pylint: disable=redefined-builtin
    def __init__(
        self,
        infile=None,
        elements=None,
        format="A4",
        orientation="portrait",
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
        if infile:
            warnings.warn(
                '"infile" is unused and will soon be deprecated',
                PendingDeprecationWarning,
            )
        if elements:
            self.load_elements(elements)
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
        pdf = self.pdf = FPDF(format=format, orientation=orientation, unit="mm")
        pdf.set_title(title)
        pdf.set_author(author)
        pdf.set_creator(creator)
        pdf.set_subject(subject)
        pdf.set_keywords(keywords)

    def load_elements(self, elements):
        """Initialize the internal element structures"""
        self.pg_no = 0
        self.elements = elements
        self.keys = [v["name"].lower() for v in self.elements]

    def parse_csv(self, infile, delimiter=",", decimal_sep="."):
        """Parse template format csv file and create elements dict"""
        keys = (
            "name",
            "type",
            "x1",
            "y1",
            "x2",
            "y2",
            "font",
            "size",
            "bold",
            "italic",
            "underline",
            "foreground",
            "background",
            "align",
            "text",
            "priority",
            "multiline",
        )
        self.elements = []
        self.pg_no = 0
        with open(infile) as f:
            for row in csv.reader(f, delimiter=delimiter):
                kargs = {}
                for i, v in enumerate(row):
                    if not v.startswith("'") and decimal_sep != ".":
                        v = v.replace(decimal_sep, ".")
                    stripped_value = v.strip()
                    typed_value = try_to_type(stripped_value)
                    kargs[keys[i]] = typed_value
                self.elements.append(kargs)
        self.keys = [v["name"].lower() for v in self.elements]

    def add_page(self):
        self.pg_no += 1
        self.texts[self.pg_no] = {}

    def __setitem__(self, name, value):
        if name.lower() not in self.keys:
            raise FPDFException(f"Element not loaded, cannot set item: {name}")
        if not self.pg_no:
            raise FPDFException("No page open, you need to call add_page() first")
        self.texts[self.pg_no][name.lower()] = value

    # setitem shortcut (may be further extended)
    set = __setitem__

    def __contains__(self, name):
        return name.lower() in self.keys

    def __getitem__(self, name):
        if not self.pg_no:
            raise FPDFException("No page open, you need to call add_page() first")
        if name not in self.keys:
            return None
        key = name.lower()
        if key in self.texts[self.pg_no]:
            # text for this page:
            return self.texts[self.pg_no][key]
        # find first element for default text:
        return next(
            (x["text"] for x in self.elements if x["name"].lower() == key), None
        )

    def split_multicell(self, text, element_name):
        """Divide (\n) a string using a given element width"""
        pdf = self.pdf
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
        pdf.set_font(element["font"], style, element["size"])
        align = {"L": "L", "R": "R", "I": "L", "D": "R", "C": "C", "": ""}.get(
            element["align"]
        )  # D/I in spanish
        text = str(text)
        return pdf.multi_cell(
            w=element["x2"] - element["x1"],
            h=element["y2"] - element["y1"],
            txt=text,
            align=align,
            split_only=True,
        )

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
        pdf = self.pdf
        for pg in range(1, self.pg_no + 1):
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.set_auto_page_break(False, margin=0)

            sorted_elements = sorted(self.elements, key=lambda x: x["priority"])

            for element in sorted_elements:
                element = element.copy()
                element["text"] = self.texts[pg].get(
                    element["name"].lower(), element["text"]
                )
                handler_name = element["type"].upper()
                if "rotate" in element:
                    with pdf.rotation(element["rotate"], element["x1"], element["y1"]):
                        self.handlers[handler_name](pdf, **element)
                else:
                    self.handlers[handler_name](pdf, **element)
        if outfile:
            pdf.output(outfile)

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
        backgroud=65535,
        multiline=None,
        **__,
    ):
        if not text:
            return
        if pdf.text_color != rgb(foreground):
            pdf.set_text_color(*rgb(foreground))
        if pdf.fill_color != rgb(backgroud):
            pdf.set_fill_color(*rgb(backgroud))

        font = font.strip().lower()
        if font == "helvetica black":
            font = "helvetica"
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
        align = {"L": "L", "R": "R", "I": "L", "D": "R", "C": "C", "": ""}.get(
            align
        )  # D/I in spanish
        pdf.set_font(font, style, size)
        # m_k = 72 / 2.54
        # h = (size/m_k)
        pdf.set_xy(x1, y1)
        if multiline is None:
            # multiline==None: write without wrapping/trimming (default)
            pdf.cell(w=x2 - x1, h=y2 - y1, txt=text, border=0, ln=0, align=align)
        elif multiline:
            # multiline==True: automatic word - warp
            pdf.multi_cell(w=x2 - x1, h=y2 - y1, txt=text, border=0, align=align)
        else:
            # multiline==False: trim to fit exactly the space defined
            text = pdf.multi_cell(
                w=x2 - x1, h=y2 - y1, txt=text, align=align, split_only=True
            )[0]
            print(f"trimming: *{text}*")
            pdf.cell(w=x2 - x1, h=y2 - y1, txt=text, border=0, ln=0, align=align)

            # pdf.Text(x=x1,y=y1,txt=text)

    @staticmethod
    def line(pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, foreground=0, **__):
        if pdf.draw_color != rgb(foreground):
            # print "SetDrawColor", hex(foreground)
            pdf.set_draw_color(*rgb(foreground))
        # print "SetLineWidth", size
        pdf.set_line_width(size)
        pdf.line(x1, y1, x2, y2)

    @staticmethod
    def rect(
        pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, foreground=0, backgroud=65535, **__
    ):
        if pdf.draw_color != rgb(foreground):
            pdf.set_draw_color(*rgb(foreground))
        if pdf.fill_color != rgb(backgroud):
            pdf.set_fill_color(*rgb(backgroud))
        pdf.set_line_width(size)
        pdf.rect(x1, y1, x2 - x1, y2 - y1)

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
        if pdf.draw_color != rgb(foreground):
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
        size=1,
        bold=False,
        italic=False,
        underline=False,
        align="",
        link="http://example.com",
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        if pdf.text_color != rgb(foreground):
            pdf.set_text_color(*rgb(foreground))
        font = font.strip().lower()
        if font == "helvetica black":
            font = "helvetica"
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
        align = {"L": "L", "R": "R", "I": "L", "D": "R", "C": "C", "": ""}.get(
            align
        )  # D/I in spanish
        pdf.set_font(font, style, size)
        # m_k = 72 / 2.54
        # h = (size/m_k)
        pdf.set_xy(x1, y1)
        pdf.write(5, text, link)
