#!/usr/bin/env python3

# USAGE: ./add_on_page.py $in_filepath $out_filepath
# Inspired by https://github.com/pmaupin/pdfrw/blob/master/examples/watermark.py

import sys
from fpdf import FPDF
from pdfrw import PageMerge, PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 1
UNDERNEATH = (
    False  # if True, new content will be placed underneath page (painted first)
)


def new_content():
    fpdf = FPDF()
    fpdf.add_page()
    fpdf.set_font("helvetica", size=36)
    fpdf.text(50, 50, "Hello!")
    reader = PdfReader(fdata=bytes(fpdf.output()))
    return reader.pages[0]


writer = PdfWriter(trailer=PdfReader(IN_FILEPATH))
PageMerge(writer.pagearray[ON_PAGE_INDEX]).add(
    new_content(), prepend=UNDERNEATH
).render()
writer.write(OUT_FILEPATH)
