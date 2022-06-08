import os
from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.skipif(
    "RUN_NETWORK_TESTS" not in os.environ, reason="skip network tests by default"
)
def test_png_url(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    png = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
    pdf.image(png, x=15, y=15, w=30, h=25)
    assert_pdf_equal(pdf, HERE / "image_png_url.pdf", tmp_path)
