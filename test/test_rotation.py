from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_rotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x, y = 60, 60
    img_filepath = HERE / "image/png_images/66ac49ef3f48ac9482049e1ab57a53e9.png"
    with pdf.rotation(45, x=x, y=y):
        pdf.image(img_filepath, x=x, y=y)
    pdf.image(img_filepath, x=150, y=150)
    assert_pdf_equal(pdf, HERE / "rotation.pdf", tmp_path)


def test_prevent_some_methods_in_rotation():  # issue-226
    pdf = FPDF()
    pdf.add_page()
    with pdf.rotation(90):
        with pytest.raises(FPDFException):
            pdf.add_page()
        with pytest.raises(FPDFException):
            pdf.set_font("Times")
        with pytest.raises(FPDFException):
            pdf.set_font_size(16)
        with pytest.raises(FPDFException):
            pdf.set_draw_color(255)
        with pytest.raises(FPDFException):
            pdf.set_fill_color(255)
        with pytest.raises(FPDFException):
            pdf.set_text_color(255)
        with pytest.raises(FPDFException):
            pdf.set_line_width(2)
        with pytest.raises(FPDFException):
            pdf.set_stretching(10)
