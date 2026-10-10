#!/usr/bin/env python3
# USAGE: ./csv2table.py color_srgb.csv
import csv, sys
from fpdf import FPDF, FontFace
from fpdf.drawing_primitives import color_from_hex_string

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=22)
with pdf.table() as table:
    with open(sys.argv[1], encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        for i, row in enumerate(reader):
            style = None
            if i > 0:
                # We color the row based on the hexadecimal code in the 2nd column:
                style = FontFace(fill_color=color_from_hex_string(row[1]))
            table.row(row, style=style)
pdf.output("from-csv.pdf")
