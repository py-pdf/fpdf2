#!/usr/bin/env python3
# Script Dependencies:
#    odfpy
# USAGE: ./ods2table.py color_srgb.ods
import sys
from fpdf import FPDF, FontFace
from fpdf.drawing import color_from_hex_string
from odf.opendocument import load
from odf.table import Table, TableCell, TableRow

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=22)
ods = load(sys.argv[1])
for sheet in ods.getElementsByType(Table):
    with pdf.table() as table:
        for i, row in enumerate(sheet.getElementsByType(TableRow)):
            row = [str(cell) for cell in row.getElementsByType(TableCell)]
            style = None
            if i > 0:
                # We color the row based on the hexadecimal code in the 2nd column:
                style = FontFace(fill_color=color_from_hex_string(row[1]))
            table.row(row, style=style)
pdf.output("from-ods.pdf")
