from pathlib import Path

import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.xfail(
    reason="Implementation not finished, cf. https://github.com/PyFPDF/fpdf2/issues/62"
)
def test_linearization(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(
        HERE / "image/png_images/66ac49ef3f48ac9482049e1ab57a53e9.png", x=150, y=150
    )
    assert_pdf_equal(pdf, HERE / "linearization.pdf", tmp_path, linearize=True)
