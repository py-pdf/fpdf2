#!/usr/bin/env python3
import io, sys

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 0  # Index of the target page (starts at zero)


def new_content():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", "B", 30)
    pdf.text(50, 150, "Hello World!")
    return io.BytesIO(pdf.output())


reader = PdfReader(IN_FILEPATH)
page_overlay = PdfReader(new_content()).pages[0]
reader.pages[ON_PAGE_INDEX].merge_page(page2=page_overlay)

writer = PdfWriter()
writer.append_pages_from_reader(reader)
writer.write(OUT_FILEPATH)
