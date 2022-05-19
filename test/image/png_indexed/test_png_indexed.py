from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal
from PIL import Image


HERE = Path(__file__).resolve().parent


def test_png_indexed_files(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # palette images (P)
    pdf.image(HERE / "palette_1.png", x=10, y=10, w=50, h=50, link=None)
    pdf.image(HERE / "palette_2.png", x=80, y=10, w=50, h=50, link=None)
    pdf.image(HERE / "palette_3.png", x=150, y=10, w=50, h=50, link=None)

    # palette with alpha images (PA)
    pdf.image(
        Image.open(HERE / "palette_1.png").convert("PA"),
        x=10,
        y=80,
        w=50,
        h=50,
        link=None,
    )
    pdf.image(
        Image.open(HERE / "palette_2.png").convert("PA"),
        x=80,
        y=80,
        w=50,
        h=50,
        link=None,
    )
    pdf.image(
        Image.open(HERE / "palette_3.png").convert("PA"),
        x=150,
        y=80,
        w=50,
        h=50,
        link=None,
    )

    assert_pdf_equal(pdf, HERE / "image_png_indexed.pdf", tmp_path)
