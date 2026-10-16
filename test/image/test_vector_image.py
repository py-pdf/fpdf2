from io import BytesIO
from pathlib import Path

import pytest
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import errors

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
    pdf = fpdf.FPDF(format=(350, 350))
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
    fname = "simple_rect_no_viewbox_nor_width_and_height.svg"
    with pytest.raises(ValueError) as error:
        pdf.image(SVG_SRCDIR / fname)
    assert fname in str(error.value)
    with pytest.raises(ValueError) as error:
        pdf.image(SVG_SRCDIR / fname, w=60)


def test_svg_image_with_unsupported_color():
    pdf = fpdf.FPDF()
    pdf.add_page()
    fname = "unsupported-color.svg"
    with pytest.raises(ValueError) as error:
        pdf.image(SVG_SRCDIR / fname)
    assert fname in str(error.value)


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


@pytest.mark.parametrize("as_stream", [False, True])
@pytest.mark.parametrize(
    "prefix",
    [
        b"<svg\n",
        b"<svg\t",
        b"\xef\xbb\xbf<svg ",
        b'<?xml\nversion="1.0"?>\n<svg ',
    ],
)
def test_svg_image_from_bytes_with_xml_whitespace(tmp_path, as_stream, prefix):
    data = (
        prefix
        + b'width="180" height="180" xmlns="http://www.w3.org/2000/svg">'
        + b'<rect x="60" y="60" width="60" height="60"/></svg>'
    )
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(BytesIO(data) if as_stream else data)
    assert_pdf_equal(pdf, HERE / "svg_image_from_bytesio.pdf", tmp_path)


def test_svg_image_billion_laughs():
    "cf. https://docs.python.org/3/library/xml.html#xml-security"
    # Potential expansion: 30 MB, bounded even on an unprotected runtime.
    declarations = ['<!ENTITY e0 "lol">']
    for level in range(1, 8):
        references = f"&e{level - 1};" * 10
        declarations.append(f'<!ENTITY e{level} "{references}">')
    svg = (
        '<?xml version="1.0"?>'
        f'<!DOCTYPE svg [{"".join(declarations)}]>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<desc>&e7;</desc><rect width="10" height="10"/></svg>'
    ).encode("utf-8")
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ParseError) as exc:
        pdf.image(BytesIO(svg))
    # Expat populates these module attributes dynamically.
    # pylint: disable-next=no-member
    assert exc.value.code == errors.codes[errors.XML_ERROR_AMPLIFICATION_LIMIT_BREACH]


def test_svg_image_quadratic_entity_expansion():
    # Repeat one large entity without nesting: potential expansion is 32 MiB.
    entity = "x" * 4096
    references = "&large;" * 8192
    svg = (
        '<?xml version="1.0"?>'
        f'<!DOCTYPE svg [<!ENTITY large "{entity}">]>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        f"<desc>{references}</desc>"
        '<rect width="10" height="10"/>'
        "</svg>"
    ).encode("utf-8")

    pdf = fpdf.FPDF()
    pdf.add_page()

    with pytest.raises(ParseError) as exc:
        pdf.image(BytesIO(svg))

    # Expat populates these module attributes dynamically.
    # pylint: disable-next=no-member
    assert exc.value.code == errors.codes[errors.XML_ERROR_AMPLIFICATION_LIMIT_BREACH]


@pytest.mark.parametrize("resource", ["file", "http"])
def test_svg_image_external_entity(tmp_path, resource):
    sentinel = tmp_path / "entity.txt"
    sentinel.write_text("EXTERNAL_ENTITY_SENTINEL", encoding="utf-8")
    uri = sentinel.as_uri() if resource == "file" else "http://127.0.0.1:9/entity.txt"
    svg = (
        '<?xml version="1.0"?>'
        f'<!DOCTYPE svg [<!ENTITY external SYSTEM "{uri}">]>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<desc>&external;</desc><rect width="10" height="10"/></svg>'
    ).encode("utf-8")
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ParseError) as exc:
        pdf.image(BytesIO(svg))
    # Expat populates these module attributes dynamically.
    # pylint: disable-next=no-member
    assert exc.value.code == errors.codes[errors.XML_ERROR_UNDEFINED_ENTITY]


def test_svg_image_bounded_internal_entity():
    svg = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE svg [<!ENTITY size "10">]>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<rect width="&size;" height="&size;"/></svg>'
    ).encode("utf-8")
    pdf = fpdf.FPDF()
    pdf.add_page()
    image = pdf.image(BytesIO(svg))
    assert image.rendered_width == 10
    assert image.rendered_height == 10


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
