# pylint: disable=redefined-outer-name, protected-access
import io
from pathlib import Path

import fpdf
from ..conftest import assert_pdf_equal

from defusedxml.ElementTree import fromstring as parse_xml_str
import pytest


from . import parameters

GENERATED_PDF_DIR = Path(__file__).resolve().parent / "generated_pdf"


def assert_style_match(lhs, rhs):
    mismatches = []
    for attr in lhs.MERGE_PROPERTIES:
        left = getattr(lhs, attr)
        right = getattr(rhs, attr)
        # can't short circuit because we want to report all of the issues
        if left != right:
            mismatches.append(f"left.{attr} ({left}) != right.{attr} ({right})")

    if mismatches:
        raise AssertionError("Styles do not match:\n    " + "\n    ".join(mismatches))


class TestUnits:
    @pytest.mark.parametrize(
        "name", [pytest.param(name, id=name) for name in fpdf.svg.relative_length_units]
    )
    def test_resolve_relative_length_units(self, name):
        with pytest.raises(ValueError):
            fpdf.svg.resolve_length(f" 1{name}")

    @pytest.mark.parametrize(
        "name", [pytest.param(name, id=name) for name in fpdf.svg.absolute_length_units]
    )
    def test_resolve_good_length_units(self, name):
        computed = fpdf.svg.resolve_length(f"  1 {name} ")
        assert isinstance(computed, float)

    def test_resolve_bad_length_units(self):
        with pytest.raises(ValueError):
            fpdf.svg.resolve_length("1 fake")

    def test_resolve_implicit_length_units(self):
        value = 1.5
        assert fpdf.svg.resolve_length(f"{value}") == value

    def test_resolve_angle_bad_units(self):
        with pytest.raises(ValueError):
            fpdf.svg.resolve_angle("1 fake")

    @pytest.mark.parametrize(
        "name", [pytest.param(name, id=name) for name in fpdf.svg.angle_units]
    )
    def test_resolve_good_angle_units(self, name):
        computed = fpdf.svg.resolve_angle(f"  1 {name} ")
        assert isinstance(computed, float)


def test_xmlns_lookup_failure():
    result = fpdf.svg.xmlns("this is not a real xml namespace", "rect")
    assert result == "rect"


def test_optional_converter():
    canary = object()
    conv = fpdf.svg.optional(object(), converter=lambda val: canary)
    assert conv is canary


class TestSVGPathParsing:
    @pytest.mark.parametrize("path, result", parameters.svg_path_directives)
    def test_parsing_all_directives(self, path, result):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        assert result == pdf_path._root_graphics_context.path_items

    @pytest.mark.parametrize("path, result", parameters.svg_path_implicit_directives)
    def test_parsing_all_implicit_directives(self, path, result):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        assert result == pdf_path._root_graphics_context.path_items

    @pytest.mark.parametrize("path, result", parameters.svg_path_edge_cases)
    def test_parsing_edge_cases(self, path, result):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        assert result == pdf_path._root_graphics_context.path_items

    def test_bad_path_start(self):
        pdf_path = fpdf.drawing.PaintedPath()

        with pytest.raises(ValueError):
            fpdf.svg.svg_path_converter(pdf_path, "L 1 2")

    @pytest.mark.parametrize(
        "debug", (pytest.param(False, id="no debug"), pytest.param(True, id="debug"))
    )
    @pytest.mark.parametrize("path, expected", parameters.svg_path_render_tests)
    def test_rendering_smooth_curves(self, debug, path, expected):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        style = fpdf.drawing.GraphicsStyle()
        first_point = fpdf.drawing.Point(0, 0)
        start = fpdf.drawing.Move(first_point)

        if debug:
            dbg = io.StringIO()
            result = pdf_path.render_debug(gsdr, style, start, first_point, dbg, "")[0]
        else:
            result = pdf_path.render(gsdr, style, start, first_point)[0]

        assert result == expected


@pytest.mark.parametrize("shape, output, guard", parameters.test_svg_shape_tags)
def test_svg_shape_conversion(shape, output, guard):
    xml = parse_xml_str(shape)
    converter = getattr(fpdf.svg.ShapeBuilder, xml.tag)

    with guard:
        path = converter(xml)
        assert output == path._root_graphics_context.path_items


class TestSVGAttributeConversion:
    @pytest.mark.parametrize(
        "transform, expected, guard", parameters.test_svg_transforms
    )
    def test_svg_transform_conversion(self, transform, expected, guard):
        with guard:
            result = fpdf.svg.convert_transforms(transform)
            assert result == pytest.approx(expected)

    @pytest.mark.parametrize("svg_file", parameters.test_svg_transform_documents)
    def test_svg_transform_conversion_visual(self, tmp_path, svg_file):
        # this only tests the SVG 1.1 transforms for now because the 2.0 transforms do not seem to be widely supported?
        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.add_page()

        svg.draw_to_page(pdf)

        assert_pdf_equal(
            pdf, GENERATED_PDF_DIR / "transforms" / f"{svg_file.stem}.pdf", tmp_path
        )

    @pytest.mark.parametrize(
        "element, expected, guard", parameters.test_svg_attribute_conversion
    )
    def test_attribute_conversion(self, element, expected, guard):
        xml = parse_xml_str(element)

        stylable = fpdf.drawing.PaintedPath()
        with guard:
            fpdf.svg.apply_styles(stylable, xml)
            assert_style_match(stylable.style, expected)


class TestSVGObject:
    def test_bad_root_tag(self):
        notsvg = """<sometag></sometag>"""

        with pytest.raises(ValueError):
            fpdf.svg.SVGObject(notsvg)

    @pytest.mark.parametrize(
        "svg_data, expected_dim, expected_tf, guard", parameters.svg_shape_info_tests
    )
    def test_document_shape_info(self, svg_data, expected_dim, expected_tf, guard):
        pdf = fpdf.FPDF(unit="pt", format=(10, 10))
        pdf.set_margin(0)
        pdf.add_page()

        with guard:
            svg = fpdf.svg.SVGObject(svg_data)
            width, height, base_group = svg.transform_to_page_viewport(pdf)

            assert (width, height) == pytest.approx(expected_dim)
            assert base_group.transform == pytest.approx(expected_tf)

    @pytest.mark.parametrize("svg_file", parameters.test_svg_sources)
    def test_svg_conversion(self, tmp_path, svg_file):
        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.add_page()

        svg.draw_to_page(pdf)

        assert_pdf_equal(pdf, GENERATED_PDF_DIR / f"{svg_file.stem}.pdf", tmp_path)

    @pytest.mark.parametrize("svg_file", parameters.test_svg_sources[0:1])
    def test_draw_to_page_offset(self, tmp_path, svg_file):
        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.add_page()

        svg.draw_to_page(pdf, x=5, y=5)

        assert_pdf_equal(
            pdf, GENERATED_PDF_DIR / f"{svg_file.stem}-offset.pdf", tmp_path
        )

    def test_path_def(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<defs><path id="path" d="M 0 0 L 1 2 Z"/></defs></svg>'
        )
        fpdf.svg.SVGObject(svg_data)

    def test_bad_xref(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<use transform="rotate(45)"/></svg>'
        )
        with pytest.raises(ValueError):
            fpdf.svg.SVGObject(svg_data)

    def test_missing_xref(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<use xlink:href="#missing"/></svg>'
        )
        with pytest.raises(ValueError):
            fpdf.svg.SVGObject(svg_data)

    def test_svg_conversion_no_transparency(self, tmp_path):
        svg = fpdf.svg.SVGObject.from_file(parameters.svgfile("SVG_logo.svg"))

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.allow_images_transparency = False
        pdf.add_page()

        svg.draw_to_page(pdf)

        assert_pdf_equal(
            pdf, GENERATED_PDF_DIR / "SVG_logo_notransparency.pdf", tmp_path
        )

    def test_svg_conversion_priority_styles(self, tmp_path):
        svg_file = parameters.svgfile("simple_rect.svg")

        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.allow_images_transparency = False
        pdf.add_page()

        svg.draw_to_page(pdf)

        assert_pdf_equal(pdf, GENERATED_PDF_DIR / f"{svg_file.stem}.pdf", tmp_path)
