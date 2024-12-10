#!/usr/bin/env python3
# Script Dependencies:
#    openxlsx
# USAGE: ./xlsx2table.py spreadsheet.xlsx
import sys
from fpdf import FPDF, FontFace
from fpdf.drawing import color_from_hex_string
from openpyxl import load_workbook

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=22)
wb = load_workbook(sys.argv[1])
ws = wb.active
with pdf.table() as table:
    for i, row in enumerate(ws.rows):
        # We color the row based on the hexadecimal code in the 2nd column:
        style = FontFace(fill_color=color_from_hex_string(row[1].value)) if i > 0 else None
        table.row([cell.value for cell in row], style=style)
pdf.output("from-xlsx.pdf")
