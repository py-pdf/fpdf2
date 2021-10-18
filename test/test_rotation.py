from pathlib import Path

from fpdf import FPDF
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
