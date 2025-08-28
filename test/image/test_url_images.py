import socket
import pytest

from pathlib import Path
from urllib.error import HTTPError

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
PNG_IMG_URL = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"


def test_png_url(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    try:
        pdf.image(PNG_IMG_URL, x=15, y=15, w=30, h=25)
    except (HTTPError, socket.timeout) as e:
        pytest.skip(f"Network error: {e}")
    assert_pdf_equal(pdf, HERE / "image_png_url.pdf", tmp_path)
