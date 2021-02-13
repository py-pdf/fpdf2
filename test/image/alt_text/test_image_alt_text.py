from pathlib import Path

import pytest

import fpdf
from fpdf.errors import FPDFException
from test.utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


IMG_FILE_PATH = HERE / "../image_types/insert_images_insert_png.png"


def test_image_alt_text(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    assert_pdf_equal(pdf, HERE / "image_alt_text.pdf", tmp_path)


def test_different_alt_text_for_same_image():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        pdf.image(IMG_FILE_PATH, alt_text="Some Logo")
    assert str(error.value).startswith(
        "Different image titles and/or alternative descriptions were provided for the same image"
    )


def test_same_alt_text_for_image_repeated(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    assert_pdf_equal(pdf, HERE / "same_alt_text_for_image_repeated.pdf", tmp_path)


def test_same_alt_text_for_image_repeated_on_different_pages(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    pdf.add_page()
    pdf.image(IMG_FILE_PATH, alt_text="Democratic Socialists of America Logo")
    assert_pdf_equal(
        pdf, HERE / "same_alt_text_for_image_repeated_on_different_pages.pdf", tmp_path
    )
