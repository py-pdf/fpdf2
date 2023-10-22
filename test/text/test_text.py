from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal

TEXT_SIZE, SPACING = 36, 1.15
LINE_HEIGHT = TEXT_SIZE * SPACING


HERE = Path(__file__).resolve().parent


def test_text_positioning(tmp_path):
    doc = FPDF()
    doc.add_page()
    for i in range(15):  # core font
        doc.set_font("helvetica", size=10 + 2 * i)
        x = 20
        y = 15 + 15 * i
        doc.line(x - 5, y, x + 5, y)
        doc.line(x, y - 5, x, y + 5)
        doc.text(x, y, f"{doc.font_family} {doc.font_size_pt}")
    doc.add_font("Roboto", fname=HERE / "../fonts/Roboto-Regular.ttf")
    for i in range(15):  # unicode font
        doc.set_font("Roboto", size=10 + 2 * i)
        x = 120
        y = 15 + 15 * i
        doc.line(x - 5, y, x + 5, y)
        doc.line(x, y - 5, x, y + 5)
        doc.text(x, y, f"{doc.font_family} {doc.font_size_pt}")

    assert_pdf_equal(doc, HERE / "text_positioning.pdf", tmp_path)


def test_text_stretch_spacing(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=20)
    for i, (stretch, spacing) in enumerate(
        (
            (100, 0),
            (150, 0),
            (100, 10),
            (130, 5),
            (70, 0),
            (100, -5),
            (80, -2),
        )
    ):
        doc.set_stretching(stretch)
        doc.set_char_spacing(spacing)
        doc.text(20, 20 + 10 * i, f"stretch: {stretch}; spacing: {spacing}")
    assert_pdf_equal(doc, HERE / "text_stretch_spacing.pdf", tmp_path)


def test_text_text_mode(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=40)
    doc.set_draw_color(255, 100, 0)
    doc.line_width = 2
    for i, mode in enumerate(
        (
            "FILL",
            "STROKE",
            "FILL_STROKE",
        )
    ):
        doc.text_mode = mode
        doc.text(20, 20 + 20 * i, f"Text mode: {mode}")
    assert_pdf_equal(doc, HERE / "text_text_mode.pdf", tmp_path)


def test_text_color(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=20)
    for i, color in enumerate(
        (
            (255, 100, 100),
            (255, 255, 100),
            (255, 100, 255),
            (250, 250, 250),
            (0, 0, 0),
        )
    ):
        doc.set_text_color(*color)
        doc.text(20, 20 + 10 * i, f"{color}")
    assert_pdf_equal(doc, HERE / "text_color.pdf", tmp_path)


def test_text_no_font_set():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        pdf.text(20, 20, text="Hello World!")
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(error.value) == expected_msg


def test_text_badinput():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(TypeError):
        pdf.text("x", 20, "Hello World")
    with pytest.raises(TypeError):
        pdf.text(20, "y", "Hello World")
    with pytest.raises(AttributeError):
        pdf.text(20, 20, 777)
    with pytest.raises(AttributeError):
        pdf.text(20, 20, (1, 2, 3))
    with pytest.raises(AttributeError):
        pdf.text(20, 20, None)


def test_text_deprecated_txt_arg():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    with pytest.warns(
        DeprecationWarning, match='The parameter "txt" has been renamed to "text"'
    ):
        # pylint: disable=unexpected-keyword-arg
        pdf.text(20, 20, text="Lorem ipsum Ut nostrud irure")
