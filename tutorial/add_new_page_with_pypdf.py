#!/usr/bin/env python3
import io, sys

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 2  # Index at which the page will be inserted (starts at zero)


def build_page():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", "B", 19)
    pdf.text(50, 10, "Hello World!")
    return io.BytesIO(pdf.output())


writer = PdfWriter(clone_from=IN_FILEPATH)
new_page = PdfReader(build_page()).pages[0]
writer.insert_page(new_page, index=ON_PAGE_INDEX)
writer.write(OUT_FILEPATH)
