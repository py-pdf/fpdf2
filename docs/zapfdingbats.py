#!/usr/bin/env python3
from itertools import chain
from string import digits, ascii_uppercase, ascii_lowercase
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=30)
pdf.cell(w=pdf.epw, text="ZapfDingbats", align="C")
pdf.set_margin(0)
for i, char in enumerate(
    "!\"#$%&'()*+,-./"
    + digits
    + ":;<=>?@"
    + ascii_uppercase
    + "[\\]^_`"
    + ascii_lowercase
    + "{|}~"
):
    if i % 24 == 0:
        pdf.x = pdf.l_margin = 10 + (i // 24) * 50
        pdf.y = 30
    pdf.set_font("helvetica", size=30)
    pdf.cell(text=char + " = ")
    pdf.set_font("zapfdingbats", size=30)
    pdf.cell(text=char, new_x="LMARGIN", new_y="NEXT")
for i, n in enumerate(chain(range(0x80, 0x8E), range(0xA1, 0xF0), range(0xF1, 0xFF))):
    if i % 26 == 0:
        col = i // 26
        if col % 3 == 0:
            pdf.add_page()
        pdf.x = pdf.l_margin = 10 + (col % 3) * 65
        pdf.y = 10
    pdf.set_font("helvetica", size=30)
    pdf.cell(text=f"\\u00{hex(n)[2:]} = ")
    pdf.set_font("zapfdingbats", size=30)
    pdf.cell(text=chr(n), new_x="LMARGIN", new_y="NEXT")
pdf.output("zapfdingbats.pdf")
