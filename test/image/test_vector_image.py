from io import BytesIO
from pathlib import Path

import pytest
from defusedxml.common import EntitiesForbidden

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
SVG_SRCDIR = HERE.parent / "svg/svg_sources"


def test_svg_image(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox and width=100% and height=100%:
    pdf.image(SVG_SRCDIR / "SVG_logo.svg")
    assert_pdf_equal(pdf, HERE / "svg_image.pdf", tmp_path)


def test_svg_image_fixed_dimensions(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox and width=100 and height=100:
    img = pdf.image(SVG_SRCDIR / "SVG_logo_fixed_dimensions.svg")
    assert img["rendered_width"] == 100
    assert img["rendered_height"] == 100
    assert_pdf_equal(pdf, HERE / "svg_image_fixed_dimensions.pdf", tmp_path)


def test_svg_image_no_dimensions(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox but no width/height:
    pdf.image(SVG_SRCDIR / "SVG_logo_no_dimensions.svg")
    assert_pdf_equal(pdf, HERE / "svg_image_no_dimensions.pdf", tmp_path)


def test_svg_image_no_viewbox(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has no viewbox and width=100 and height=200:
    img = pdf.image(SVG_SRCDIR / "simple_rect_no_viewbox.svg")
    assert img["rendered_width"] == 100
    assert img["rendered_height"] == 200
    assert_pdf_equal(pdf, HERE / "svg_image_no_viewbox.pdf", tmp_path)


def test_svg_image_with_custom_width(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox and width=100% and height=100%:
    img = pdf.image(SVG_SRCDIR / "SVG_logo.svg", w=60)
    assert img["rendered_width"] == 60
    assert_pdf_equal(pdf, HERE / "svg_image_with_custom_width.pdf", tmp_path)


def test_svg_image_with_custom_width_and_no_dimensions(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox but no width/height:
    img = pdf.image(SVG_SRCDIR / "SVG_logo_no_dimensions.svg", w=60)
    assert img["rendered_width"] == 60
    assert_pdf_equal(
        pdf, HERE / "svg_image_with_custom_width_and_no_dimensions.pdf", tmp_path
    )


def test_svg_image_with_custom_width_and_no_viewbox(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has no viewbox and width=100 and height=200:
    img = pdf.image(SVG_SRCDIR / "simple_rect_no_viewbox.svg", w=60)
    assert img["rendered_width"] == 60
    assert_pdf_equal(
        pdf, HERE / "svg_image_with_custom_width_and_no_viewbox.pdf", tmp_path
    )


def test_svg_image_with_no_dimensions_and_custom_width(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox but no width/height:
    img = pdf.image(SVG_SRCDIR / "SVG_logo_no_dimensions.svg", w=60)
    assert img["rendered_width"] == 60
    assert_pdf_equal(
        pdf, HERE / "svg_image_with_no_dimensions_and_custom_width.pdf", tmp_path
    )


def test_svg_image_with_custom_size(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has a 300x300 viewbox but no width/height:
    pdf.image(SVG_SRCDIR / "SVG_logo_no_dimensions.svg", x=50, y=50, w=30, h=60)
    pdf.rect(x=50, y=50, w=30, h=60)  # Displays the bounding box
    assert_pdf_equal(pdf, HERE / "svg_image_with_custom_size.pdf", tmp_path)


def test_svg_image_with_custom_size_and_no_viewbox(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    # This image has no viewbox and width=100 and height=200:
    img = pdf.image(SVG_SRCDIR / "simple_rect_no_viewbox.svg", x=50, y=50, w=30, h=60)
    assert img["rendered_width"] == 30
    assert img["rendered_height"] == 60
    pdf.rect(x=50, y=50, w=30, h=60)  # Displaying the bounding box
    assert_pdf_equal(
        pdf, HERE / "svg_image_with_custom_size_and_no_viewbox.pdf", tmp_path
    )


def test_svg_image_no_viewbox_nor_width_and_height():
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        pdf.image(SVG_SRCDIR / "simple_rect_no_viewbox_nor_width_and_height.svg")
    with pytest.raises(ValueError):
        pdf.image(
            SVG_SRCDIR / "simple_rect_no_viewbox_nor_width_and_height.svg",
            w=60,
        )


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


def test_svg_image_from_bytes(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(
        b'<svg width="180" height="180" xmlns="http://www.w3.org/2000/svg">'
        b'  <rect x="60" y="60" width="60" height="60"/>'
        b"</svg>"
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


def test_svg_image_fit_rect(tmp_path):
    """
    Scale the image to fill the rectangle, keeping its aspect ratio,
    and ensure it does overflow the rectangle width or height in the process.
    """
    pdf = fpdf.FPDF()
    pdf.add_page()
    test_file = SVG_SRCDIR / "SVG_logo.svg"

    rect1 = 30, 30, 60, 100
    pdf.rect(*rect1)
    pdf.image(test_file, *rect1, keep_aspect_ratio=True)

    rect2 = 100, 30, 100, 60
    pdf.rect(*rect2)
    pdf.image(test_file, *rect2, keep_aspect_ratio=True)

    assert_pdf_equal(pdf, HERE / "svg_image_fit_rect.pdf", tmp_path)


IMG_DESCRIPTION = "The Mighty SVG Logo"


def test_svg_image_alt_text_title(tmp_path):
    test_file = SVG_SRCDIR / "SVG_logo.svg"
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(test_file, alt_text=IMG_DESCRIPTION, w=50, h=50)
    pdf.image(test_file, title=IMG_DESCRIPTION, w=50, h=50)
    pdf.image(test_file, alt_text=IMG_DESCRIPTION, title=IMG_DESCRIPTION, w=50, h=50)
    assert_pdf_equal(pdf, HERE / "svg_image_alt_text_title.pdf", tmp_path)


def test_svg_image_alt_text_two_pages(tmp_path):
    test_file = SVG_SRCDIR / "SVG_logo.svg"
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(test_file, alt_text=IMG_DESCRIPTION, w=50, h=50)
    pdf.add_page()
    pdf.image(test_file, alt_text=IMG_DESCRIPTION, w=50, h=50)
    assert_pdf_equal(pdf, HERE / "svg_image_alt_text_two_pages.pdf", tmp_path)
