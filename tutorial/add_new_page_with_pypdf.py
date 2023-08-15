#!/usr/bin/env python3
import io, sys

from fpdf import FPDF
from PyPDF2 import PdfMerger

IN_FILEPATH = sys.argv[1]
OUT_FILEPATH = sys.argv[2]
ON_PAGE_INDEX = 2  # Index at which the page will be inserted (starts at zero)


def new_page():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", "B", 19)
    pdf.text(50, 10, "Hello World!")
    return io.BytesIO(pdf.output())


merger = PdfMerger()
merger.merge(position=0, fileobj=IN_FILEPATH)
merger.merge(position=ON_PAGE_INDEX, fileobj=new_page())
merger.write(OUT_FILEPATH)
