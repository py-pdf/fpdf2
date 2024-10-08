from pathlib import Path

from fpdf import FPDF
from fpdf.image_parsing import get_img_info
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
IMAGE_PATH = HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"


def test_full_width_image(tmp_path):  # issue-166
    img = get_img_info(IMAGE_PATH)
    pdf = FPDF(format=(img["w"], img["h"]))
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=img["w"])
    assert_pdf_equal(pdf, HERE / "full_width_image.pdf", tmp_path)


def test_full_height_image(tmp_path):  # issue-166
    img = get_img_info(IMAGE_PATH)
    pdf = FPDF(format=(img["w"], img["h"]))
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(IMAGE_PATH, h=img["h"])
    assert_pdf_equal(pdf, HERE / "full_height_image.pdf", tmp_path)


def test_full_pdf_width_image(tmp_path):  # issue-528
    pdf = FPDF()
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png", w=pdf.epw)
    assert_pdf_equal(pdf, HERE / "full_pdf_width_image.pdf", tmp_path)


def test_full_pdf_height_image(tmp_path):  # issue-528
    pdf = FPDF()
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(HERE / "png_images/51a4d21670dc8dfa8ffc9e54afd62f5f.png", h=pdf.eph)
    assert_pdf_equal(pdf, HERE / "full_pdf_height_image.pdf", tmp_path)


def test_image_with_explicit_dimensions(tmp_path):
    pdf = FPDF()
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(
        HERE / "png_images/6c853ed9dacd5716bc54eb59cec30889.png",
        w=pdf.epw,
        dims=(500, 500),
    )
    assert_pdf_equal(pdf, HERE / "image_with_explicit_dimensions.pdf", tmp_path)
