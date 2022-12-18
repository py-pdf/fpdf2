from io import BytesIO
from pathlib import Path

import pytest
from defusedxml.common import EntitiesForbidden

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
    pdf.image(
        HERE / "../svg/svg_sources/SVG_logo_no_dimensions.svg", x=50, y=50, w=30, h=60
    )
    pdf.rect(x=50, y=50, w=30, h=60)  # Displaying the bounding box
    assert_pdf_equal(pdf, HERE / "svg_image_with_custom_size.pdf", tmp_path)


def test_svg_image_style_inherited_from_fpdf(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_draw_color(255, 128, 0)
    pdf.set_fill_color(0, 128, 255)
    pdf.image(
        BytesIO(
            b'<svg width="180" height="180" xmlns="http://www.w3.org/2000/svg">'
            b'  <rect x="60" y="60" width="60" height="60" stroke-width="2"/>'
            b"</svg>"
        )
    )
    assert_pdf_equal(pdf, HERE / "svg_image_style_inherited_from_fpdf.pdf", tmp_path)


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
            b'<svg width="180" height="180" xmlns="http://www.w3.org/2000/svg">'
            b'  <rect x="60" y="60" width="60" height="60"/>'
            b"</svg>"
        )
    )
    assert_pdf_equal(pdf, HERE / "svg_image_from_bytesio.pdf", tmp_path)


def test_svg_image_billion_laughs():
    "cf. https://pypi.org/project/defusedxml/#attack-vectors"
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(EntitiesForbidden):
        pdf.image(
            BytesIO(
                b'<?xml version="1.0"?>'
                b"<!DOCTYPE lolz ["
                b'  <!ENTITY lol "lol">'
                b"  <!ELEMENT lolz (#PCDATA)>"
                b'  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
                b'  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">'
                b'  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">'
                b'  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">'
                b'  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">'
                b'  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">'
                b'  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">'
                b'  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">'
                b'  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">'
                b"]>"
                b"<lolz>&lol9;</lolz>"
            )
        )
