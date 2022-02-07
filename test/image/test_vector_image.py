from io import BytesIO
from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_svg_image(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(HERE / "../svg/svg_sources/SVG_logo.svg")
    assert_pdf_equal(pdf, HERE / "svg_image.pdf", tmp_path)


def test_svg_image_with_custom_width(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(HERE / "../svg/svg_sources/SVG_logo.svg", w=60)
    assert_pdf_equal(pdf, HERE / "svg_image_with_custom_width.pdf", tmp_path)


def test_svg_image_no_dimensions():
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        pdf.image(HERE / "../svg/svg_sources/SVG_logo_no_dimensions.svg")


def test_svg_image_with_custom_size(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(HERE / "../svg/svg_sources/SVG_logo_no_dimensions.svg", w=30, h=60)
    assert_pdf_equal(pdf, HERE / "svg_image_with_custom_size.pdf", tmp_path)


def test_svg_image_fixed_dimensions(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(HERE / "../svg/svg_sources/SVG_logo_fixed_dimensions.svg")
    assert_pdf_equal(pdf, HERE / "svg_image_fixed_dimensions.pdf", tmp_path)


def test_svg_image_from_bytesio(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(
        BytesIO(
            b'<svg width="180" height="180" xmlns="http://www.w3.org/2000/svg"><rect x="60" y="60" width="60" height="60"/></svg>'
        )
    )
    assert_pdf_equal(pdf, HERE / "svg_image_from_bytesio.pdf", tmp_path)
