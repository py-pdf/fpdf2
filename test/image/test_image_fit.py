from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_image_fit_in_rect(tmp_path):
    """
    Scale the image to fill the rectangle, keeping its aspect ratio,
    and ensure it does overflow the rectangle width or height in the process.
    """
    pdf = FPDF()
    pdf.add_page()

    rect1 = 30, 30, 60, 100
    pdf.rect(*rect1)
    pdf.image(
        HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png",
        *rect1,
        keep_aspect_ratio=True
    )

    rect2 = 100, 30, 60, 100
    pdf.rect(*rect2)
    pdf.image(
        HERE / "png_images/51a4d21670dc8dfa8ffc9e54afd62f5f.png",
        *rect2,
        keep_aspect_ratio=True
    )

    assert_pdf_equal(pdf, HERE / "image_fit_in_rect.pdf", tmp_path)
