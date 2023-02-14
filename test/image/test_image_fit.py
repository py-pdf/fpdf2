from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_image_fit_in_rect(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    rect1 = 30, 30, 60, 100
    pdf.rect(*rect1)
    fit_image_vertically_in_rect(
        pdf, HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png", *rect1
    )

    rect2 = 100, 30, 60, 100
    pdf.rect(*rect2)
    fit_image_vertically_in_rect(
        pdf, HERE / "png_images/51a4d21670dc8dfa8ffc9e54afd62f5f.png", *rect2
    )

    assert_pdf_equal(pdf, HERE / "image_fit_in_rect.pdf", tmp_path)


def fit_image_vertically_in_rect(pdf, img_path, x, y, w, h):
    """
    Scale the image vertically to fill the rectangle height, keeping its aspect ratio,
    and ensure it does overflow the rectangle width in the process.
    """
    _, _, img_info = pdf.preload_image(img_path)
    ratio = img_info.width / img_info.height
    if h * ratio < w:
        x += (w - h * ratio) / 2
        w = h * ratio
    else:  # => too wide, limiting width:
        y += (h - w / ratio) / 2
        h = w / ratio
    pdf.image(img_path, x=x, y=y, w=w, h=h)
