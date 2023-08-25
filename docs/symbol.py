#!/usr/bin/env python3
from itertools import chain
import fpdf

pdf = fpdf.FPDF()
pdf.set_margin(0)
for i, n in enumerate(chain(range(0x21, 0x81), range(0xA0, 0xFF))):
    if i % 25 == 0:
        col = i // 25
        if col % 3 == 0:
            pdf.l_margin = 0
            pdf.add_page()
            pdf.set_font("helvetica", size=30)
            pdf.y = 10
            pdf.cell(w=pdf.epw, text="Symbol font", align="C")
        pdf.x = pdf.l_margin = 10 + (col % 3) * 65
        pdf.y = 30
    pdf.set_font("helvetica", size=30)
    pdf.cell(text=f"\\u00{hex(n)[2:]} = ")
    pdf.set_font("symbol", size=30)
    pdf.cell(text=chr(n), ln=1)
pdf.output("symbol.pdf")
