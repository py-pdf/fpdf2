from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
IMAGE_PATH = HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"


def test_full_width_image(tmp_path):  # issue-166
    img = fpdf.image_parsing.get_img_info(IMAGE_PATH)
    pdf = fpdf.FPDF(format=(img["w"], img["h"]))
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=img["w"])
    assert_pdf_equal(pdf, HERE / "full_width_image.pdf", tmp_path)


def test_full_height_image(tmp_path):  # issue-166
    img = fpdf.image_parsing.get_img_info(IMAGE_PATH)
    pdf = fpdf.FPDF(format=(img["w"], img["h"]))
    pdf.set_margin(0)
    pdf.add_page()
    pdf.image(IMAGE_PATH, h=img["h"])
    assert_pdf_equal(pdf, HERE / "full_height_image.pdf", tmp_path)
