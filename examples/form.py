# -*- coding: iso-8859-1 -*-
import sys, os
from fpdf import FPDF


class Form:
    def __init__(self, infile):
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
        )
        # parse form format file and create fields dict
        self.fields = {}
        with open(infile) as file:
            for linea in file.readlines():
                kargs = {}
                for i, v in enumerate(linea.split(";")):
                    if not v.startswith("'"):
                        v = v.replace(",", ".")
                    else:
                        v = v  # .decode('latin1')
                    if v == "":
                        v = None
                    else:
                        v = eval(v.strip())
                    kargs[keys[i]] = v
                self.fields[kargs["name"].lower()] = kargs
        self.handlers = {
            "T": self.text,
            "L": self.line,
            "I": self.image,
            "B": self.rect,
            "BC": self.barcode,
        }

    def set(self, name, value):
        if name.lower() in self.fields:
            self.fields[name.lower()]["text"] = value

    def render(self, outfile):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)

        for field in self.fields.values():
            self.handlers[field["type"].upper()](pdf, **field)

        pdf.output(outfile, "F")

    def text(
        self,
        pdf,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="arial",
        size=10,
        bold=False,
        italic=False,
        underline=False,
        align="",
        *args,
        **kwargs
    ):
        if text:
            font = font.strip().lower()
            if font == "arial black":
                font = "arial"
            style = ""
            if bold:
                style += "B"
            if italic:
                style += "I"
            if underline:
                style += "U"
            align = {"I": "L", "D": "R", "C": "C", "": "", None: None}[align]
            pdf.set_font(font, style, size)
            ##m_k = 72 / 2.54
            ##h = (size/m_k)
            pdf.set_xy(x1, y1)
            pdf.cell(w=x2 - x1, h=y2 - y1, txt=text, border=0, ln=0, align=align)
            # pdf.Text(x=x1,y=y1,txt=text)

    def line(self, pdf, x1=0, y1=0, x2=0, y2=0, size=0, *args, **kwargs):
        pdf.set_line_width(size)
        pdf.line(x1, y1, x2, y2)

    def rect(self, pdf, x1=0, y1=0, x2=0, y2=0, size=0, *args, **kwargs):
        pdf.set_line_width(size)
        pdf.rect(x1, y1, x2 - x1, y2 - y1)

    def image(self, pdf, x1=0, y1=0, x2=0, y2=0, text="", *args, **kwargs):
        pdf.image(text, x1, y1, w=x2 - x1, h=y2 - y1, type="", link="")

    def barcode(
        self,
        pdf,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="arial",
        size=1,
        *args,
        **kwargs
    ):
        font = font.lower().strip()
        if font == "interleaved 2of5 nt":
            pdf.interleaved2of5(text, x1, y1, w=size)


if __name__ == "__main__":
    f = Form("invoice.csv")
    f.set("EMPRESA", "Saraza")
    f.set("logo", "logo.png")
    f.render("./invoice.pdf")
    if sys.platform.startswith("linux"):
        os.system("xdg-open ./invoice.pdf")
    else:
        os.system("./invoice.pdf")
