from pathlib import Path

from fpdf import Align, FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
IMAGE_PATH = HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"


def test_image_x_align_center(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(IMAGE_PATH, x="C")
    pdf.image(IMAGE_PATH, x=Align.C)
    assert_pdf_equal(pdf, HERE / "image_x_align_center.pdf", tmp_path)


def test_image_x_align_right(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(IMAGE_PATH, x="R")
    pdf.image(IMAGE_PATH, x=Align.R)
    assert_pdf_equal(pdf, HERE / "image_x_align_right.pdf", tmp_path)
