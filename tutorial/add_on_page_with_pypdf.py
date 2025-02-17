#!/usr/bin/env python3
# USAGE: ./add_on_page_with_pypdf.py src_file.pdf dest_file.pdf
import io, sys
from contextlib import contextmanager

# Before 2.8.2 use: from fpdf.util import get_scale_factor
from fpdf import FPDF, get_scale_factor
from pypdf import PdfReader, PdfWriter

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]


@contextmanager
def add_to_page(reader_page, unit="mm"):
    k = get_scale_factor(unit)
    format = (reader_page.mediabox[2] / k, reader_page.mediabox[3] / k)
    pdf = FPDF(format=format, unit=unit)
    pdf.add_page()
    yield pdf
    page_overlay = PdfReader(io.BytesIO(pdf.output())).pages[0]
    reader_page.merge_page(page2=page_overlay)


reader = PdfReader(IN_FILEPATH)
with add_to_page(reader.pages[0]) as pdf:
    pdf.set_font("times", style="B", size=30)
    pdf.text(50, 150, "Hello World!")

writer = PdfWriter()
writer.append_pages_from_reader(reader)
writer.write(OUT_FILEPATH)
