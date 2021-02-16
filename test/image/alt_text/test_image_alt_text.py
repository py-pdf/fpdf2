from pathlib import Path

import fpdf
from test.utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


IMG_FILE_PATH = HERE / "../image_types/insert_images_insert_png.png"
IMG_DESCRIPTION = "Democratic Socialists of America Logo"


def test_alt_text_and_title(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text=IMG_DESCRIPTION)
    pdf.image(IMG_FILE_PATH, title=IMG_DESCRIPTION)
    pdf.image(IMG_FILE_PATH, alt_text=IMG_DESCRIPTION, title=IMG_DESCRIPTION)
    assert_pdf_equal(pdf, HERE / "alt_text_and_title.pdf", tmp_path)


def test_alt_text_on_two_pages(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text=IMG_DESCRIPTION)
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text=IMG_DESCRIPTION)
    assert_pdf_equal(pdf, HERE / "test_alt_text_on_two_pages.pdf", tmp_path)
