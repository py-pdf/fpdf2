#!/usr/bin/env python3
# Script that demonstrate the use of all 14 standard (core / builtin) PDF fonts
from fpdf import FPDF
from fpdf.fonts import CORE_FONTS

pdf = FPDF()
pdf.add_page()
for core_font in CORE_FONTS:
    style = ""
    if core_font.endswith("I"):
        core_font = core_font[:-1]
        style += "I"
    if core_font.endswith("B"):
        core_font = core_font[:-1]
        style += "B"
    text = core_font.capitalize()
    if "B" in style:
        text += " Bold"
    if "I" in style:
        text += " Italics"
    if core_font in ("symbol", "zapfdingbats"):
        pdf.set_font("Helvetica", size=24)
        pdf.cell(text=text + " : ", h=9)
    pdf.set_font(core_font, style=style, size=24)
    pdf.cell(text=text, h=9)
    pdf.ln()
pdf.output("core_fonts.pdf")
