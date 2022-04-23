from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_rect_clip(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    top_left_x, top_left_y = 50, 50
    with pdf.rect_clip(x=top_left_x + 8, y=top_left_y, w=46, h=32):
        pdf.image(
            HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png",
            x=top_left_x,
            y=top_left_y,
        )

    top_left_x, top_left_y = 50, 150
    with pdf.rect_clip(x=top_left_x + 10, y=top_left_y + 34, w=34, h=20):
        pdf.image(
            HERE / "image_types/insert_images_insert_png.png",
            x=top_left_x,
            y=top_left_y,
        )

    assert_pdf_equal(pdf, HERE / "rect_clip.pdf", tmp_path)


def test_round_clip(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    top_left_x, top_left_y = 50, 50
    with pdf.round_clip(x=top_left_x + 12, y=top_left_y + 2, r=38):
        pdf.image(
            HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png",
            x=top_left_x,
            y=top_left_y,
        )

    top_left_x, top_left_y = 50, 150
    with pdf.round_clip(x=top_left_x + 12, y=top_left_y + 25, r=30):
        pdf.image(
            HERE / "image_types/insert_images_insert_png.png",
            x=top_left_x,
            y=top_left_y,
        )

    assert_pdf_equal(pdf, HERE / "round_clip.pdf", tmp_path)


def test_elliptic_clip(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    with pdf.elliptic_clip(x=90, y=50, w=100, h=60):
        pdf.image(HERE / "png_images/d2e515cfdabae699301dcf290382474d.png", w=pdf.epw)

    assert_pdf_equal(pdf, HERE / "elliptic_clip.pdf", tmp_path)
