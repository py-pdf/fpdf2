#!/usr/bin/env python3
import sys
from fpdf import FPDF
from pdfrw import PageMerge, PdfReader, PdfWriter
from pdfrw.pagemerge import RectXObj

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 1
# if True, new content will be placed underneath page (painted first):
UNDERNEATH = False

reader = PdfReader(IN_FILEPATH)
area = RectXObj(reader.pages[0])


def new_content():
    fpdf = FPDF(format=(area.w, area.h), unit="pt")
    fpdf.add_page()
    fpdf.set_font("helvetica", size=36)
    fpdf.text(50, 50, "Hello!")
    reader = PdfReader(fdata=bytes(fpdf.output()))
    return reader.pages[0]


writer = PdfWriter()
writer.pagearray = reader.Root.Pages.Kids
if writer.pagearray[0].Kids:
    writer.pagearray = writer.pagearray[0].Kids
PageMerge(writer.pagearray[ON_PAGE_INDEX]).add(
    new_content(), prepend=UNDERNEATH
).render()
writer.write(OUT_FILEPATH)
