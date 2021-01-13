"""
An example of script that generates a one page invoice with barcode,
with data coming from a CSV file.
"""
import os
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
                    if v in ("", "None"):
                        v = None
                    elif v.startswith("'"):
                        v = v.strip()[1:-1]
                    else:
                        v = float(v.replace(",", "."))
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
        pdf.set_font("helvetica", "B", 16)

        for field in self.fields.values():
            self.handlers[field["type"].upper()](pdf, **field)

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
        **__
    ):
        if text:
            font = font.strip().lower()
            if font == "helvetica black":
                font = "helvetica"
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

    @staticmethod
    def line(pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, **__):
        pdf.set_line_width(size)
        pdf.line(x1, y1, x2, y2)

    @staticmethod
    def rect(pdf, *_, x1=0, y1=0, x2=0, y2=0, size=0, **__):
        pdf.set_line_width(size)
        pdf.rect(x1, y1, x2 - x1, y2 - y1)

    @staticmethod
    def image(pdf, *_, x1=0, y1=0, x2=0, y2=0, text="", **__):
        pdf.image(text, x1, y1, w=x2 - x1, h=y2 - y1)

    @staticmethod
    def barcode(pdf, *_, x1=0, y1=0, text="", font="helvetica", size=1, **__):
        font = font.lower().strip()
        if font == "interleaved 2of5 nt":
            pdf.interleaved2of5(text, x1, y1, w=size)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    f = Form("invoice.csv")
    f.set("EMPRESA", "Saraza")
    f.set("logo", "logo.png")
    f.render("./invoice.pdf")
