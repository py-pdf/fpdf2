# pylint: disable=no-self-use, protected-access
from io import BytesIO
from pathlib import Path
import re
import zlib

import fpdf
from ..conftest import assert_pdf_equal

from xml.etree.ElementTree import fromstring as parse_xml_str
import pytest


from . import parameters

HERE = Path(__file__).resolve().parent
GENERATED_PDF_DIR = HERE / "generated_pdf"


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
        "name",
        [
            pytest.param(name, id=name)
            for name in sorted(fpdf.svg.relative_length_units)
        ],
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

    @pytest.mark.parametrize(
        "length, expected",
        [
            ("1e2pt", 100),
            ("2E+2px", 150),
            ("-2.5e-1mm", -0.25 * 72 / 25.4),
            ("1.e-1in", 7.2),
            (".5e+2cm", 50 * 72 / 2.54),
            ("1e-3", 0.001),
        ],
    )
    def test_resolve_scientific_length(self, length, expected):
        assert fpdf.svg.resolve_length(length) == pytest.approx(expected)

    @pytest.mark.parametrize("length", ["1.2.3", "1e2.3", "1e+", "-1E--2"])
    def test_resolve_invalid_scientific_length(self, length):
        with pytest.raises(ValueError):
            fpdf.svg.resolve_length(length)

    def test_resolve_scientific_angle(self):
        assert fpdf.svg.resolve_angle("1e2deg") == pytest.approx(
            fpdf.svg.resolve_angle("100deg")
        )

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
        with pytest.raises(ValueError):
            fpdf.svg.svg_path_converter(pdf_path, "C 1 2 3 4 5 6")
        with pytest.raises(ValueError):
            fpdf.svg.svg_path_converter(pdf_path, "Q 1 2 3 4")
        with pytest.raises(ValueError):
            fpdf.svg.svg_path_converter(pdf_path, "A 1 2 0 1 0 4 5")

    @pytest.mark.parametrize("path, expected", parameters.svg_path_render_tests)
    def test_rendering_smooth_curves(self, path, expected):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        resource_catalog = fpdf.output.ResourceCatalog()
        style = fpdf.drawing.GraphicsStyle()
        first_point = fpdf.drawing.Point(0, 0)
        start = fpdf.drawing.Move(first_point)

        result = pdf_path.render(resource_catalog, style, start, first_point)[0]

        # The operators must match exactly, the numbers up to their last rounded
        # digit, which can differ between environments.
        def split(rendered):
            numbers, operators = [], []
            for token in rendered.split():
                try:
                    numbers.append(float(token))
                except ValueError:
                    operators.append(token)
            return numbers, operators

        actual_numbers, actual_operators = split(result)
        expected_numbers, expected_operators = split(expected)
        assert actual_operators == expected_operators
        assert actual_numbers == pytest.approx(expected_numbers, abs=1.1e-4, rel=0)


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

    def test_svg_transform_exponents_render_like_decimals(self, tmp_path):
        pdfs = []
        for transform in ("translate(1e1,2E1) scale(2e0)", "translate(10,20) scale(2)"):
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
                f'<rect x="5" y="5" width="10" height="10" transform="{transform}"/>'
                "</svg>"
            )
            pdf = fpdf.FPDF()
            pdf.add_page()
            pdf.image(BytesIO(svg.encode()), x=10, y=10, w=50, h=50)
            pdfs.append(pdf)

        assert_pdf_equal(pdfs[0], pdfs[1], tmp_path)

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
    def test_scientific_length_attributes(self):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="1e2pt" height="5e1pt">'
            '<rect x="1e1pt" y="2E0pt" width="8e1pt" height="4.8e1pt" />'
            "</svg>"
        )
        assert svg.width == pytest.approx(100)
        assert svg.height == pytest.approx(50)
        pdf = fpdf.FPDF(unit="pt", format=(100, 50))
        pdf.set_margin(0)
        pdf.add_page()
        svg.draw_to_page(pdf)
        assert pdf.output().startswith(b"%PDF-")

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

    @pytest.mark.parametrize(
        "font_size, expected", [('font-size="20px"', 15), ('style="font-size:9pt"', 9)]
    )
    def test_document_size_em_root_font_size(self, font_size, expected):
        svg = fpdf.svg.SVGObject(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="2em" {font_size}/>'
        )
        assert (svg.width, svg.height) == (expected, 2 * expected)

    @pytest.mark.parametrize(
        "shape, expected",
        [
            ('<g font-size="10"><rect width="2em" height="1ex"/></g>', (0, 0, 20, 5)),
            ('<rect width="2em" height="1em" style="font-size:9pt"/>', (0, 0, 18, 9)),
            (
                '<g font-size="10"><g font-size="2em"><rect x="1em" width="1em" height="1em"/></g></g>',
                (20, 0, 20, 20),
            ),
            ('<rect width="1em" height="1ex"/>', (0, 0, 12, 6)),  # 16px
        ],
    )
    def test_shape_em_lengths_use_font_size(self, shape, expected):
        # as in CSS, em and ex in the lengths of a shape are relative to its font size
        svg = fpdf.svg.SVGObject(
            f'<svg xmlns="http://www.w3.org/2000/svg">{shape}</svg>'
        )
        group = svg.base_group
        while not isinstance(group.path_items[0], fpdf.drawing.PaintedPath):
            group = group.path_items[0]
        rect = group.path_items[0]._root_graphics_context.path_items[1]
        assert (rect.org.x, rect.org.y, rect.size.x, rect.size.y) == pytest.approx(
            expected
        )

    def test_clipping_path_em_lengths_use_font_size(self):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg"><clipPath id="c">'
            '<rect font-size="40" width="1em" height="1ex"/></clipPath>'
            '<rect width="5" height="5" clip-path="url(#c)"/></svg>'
        )
        rect = svg.cross_references["#c"]._root_graphics_context.path_items[1]
        assert (rect.size.x, rect.size.y) == pytest.approx((40, 20))

    def test_defs_em_lengths_use_font_size(self):
        # a shape in <defs> inherits the font size of the root, like a sibling of <defs>
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" font-size="40">'
            '<defs><rect id="r" width="1em" height="1ex"/></defs>'
            '<use xlink:href="#r"/><rect width="1em" height="1ex"/></svg>'
        )
        used, sibling = (
            item._root_graphics_context.path_items[1]
            for item in (
                svg.cross_references["#r"],
                svg.base_group.path_items[1],
            )
        )
        assert (used.size.x, used.size.y) == pytest.approx((40, 20))
        assert (sibling.size.x, sibling.size.y) == pytest.approx((40, 20))

    def test_line_em_lengths_use_font_size(self):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<line x2="1ex" y2="1em" font-size="20" stroke="red"/></svg>'
        )
        line = svg.base_group.path_items[0]._root_graphics_context.path_items
        assert (line[1].pt.x, line[1].pt.y) == pytest.approx((10, 20))

    @pytest.mark.parametrize(
        "size", ['width="auto" height="auto"', 'width="AUTO"', 'height=" auto "']
    )
    def test_document_size_auto(self, size):
        # as Figma writes it: sized like an <svg> without width and height
        svg_data = (
            f'<svg xmlns="http://www.w3.org/2000/svg" {size} viewBox="0 0 24 16"/>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        assert (svg.width, svg.height) == (None, None)

        pdf = fpdf.FPDF()
        pdf.add_page()
        info = pdf.image(BytesIO(svg_data.encode()), w=48)
        assert (info.rendered_width, info.rendered_height) == pytest.approx((48, 32))

    @pytest.mark.parametrize("whitespace", ["100% ", " 100%", " 100% ", "100%\n"])
    def test_document_shape_info_percent_surrounded_by_whitespace(self, whitespace):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{whitespace}" height="{whitespace}" viewBox="0 0 10 10"></svg>'
        )

        svg = fpdf.svg.SVGObject(svg_data)

        assert isinstance(svg.width, fpdf.svg.Percent)
        assert isinstance(svg.height, fpdf.svg.Percent)
        assert svg.width == pytest.approx(100)
        assert svg.height == pytest.approx(100)

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

    @pytest.mark.parametrize("path_data", ["", "  "])
    def test_path_empty_data(self, path_data):
        # Empty path data disables rendering of the path, like a missing "d"
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{path_data}"/><path/></svg>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        empty, missing = svg.base_group.path_items
        assert not empty._root_graphics_context.path_items
        assert not missing._root_graphics_context.path_items

    def test_path_not_starting_with_move(self):
        svg_data = '<svg xmlns="http://www.w3.org/2000/svg"><path d="L 1 2"/></svg>'
        with pytest.raises(ValueError, match="must start with a moveto"):
            fpdf.svg.SVGObject(svg_data)

    def test_nested_defs(self, caplog):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg"><defs><defs>'
            '<clipPath id="clip"><rect width="5" height="5"/></clipPath>'
            '<rect id="square" width="5" height="5"/></defs></defs>'
            '<rect width="10" height="10" clip-path="url(#clip)"/></svg>'
        )
        with caplog.at_level("WARNING"):
            svg = fpdf.svg.SVGObject(svg_data)
        assert "Ignoring" not in caplog.text
        assert "#square" in svg.cross_references
        clipping_path = svg.base_group.path_items[0].clipping_path
        assert clipping_path is svg.cross_references["#clip"]

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

    def test_svg_without_xmlns_with_unsupported_tag(self, caplog):
        # Older and hand-written SVG files often omit the xmlns declaration
        svg_data = (
            '<svg width="10" height="10"><title>A square</title>'
            '<rect width="10" height="10"/></svg>'
        )
        with caplog.at_level("WARNING"):
            svg = fpdf.svg.SVGObject(svg_data)
        assert "Ignoring unsupported SVG tag: <title>" in caplog.text
        assert len(svg.base_group.path_items) == 1

    @pytest.mark.parametrize(
        "css, style, fill",
        [
            (".a { fill: red !important }", "fill: blue", "#f00"),
            (".a { fill: red !important }", "fill: blue !important", "#00f"),
            (".a { fill: red !important } .a { fill: blue }", "", "#f00"),
            (".a { fill: red }", "fill: blue", "#00f"),
            # a property declared twice in one rule or style attribute
            ("", "fill: red !important; fill: blue", "#f00"),
            (".a { fill: red !important; fill: blue }", "", "#f00"),
            ("", "fill: red !important; fill: blue !important", "#00f"),
        ],
    )
    def test_svg_css_important(self, css, style, fill):
        # an !important declaration of a stylesheet wins over a normal inline one
        svg = fpdf.svg.SVGObject(
            f'<svg xmlns="http://www.w3.org/2000/svg"><style>{css}</style>'
            f'<rect class="a" style="{style}" width="10" height="10"/></svg>'
        )
        rect = svg.base_group.path_items[0]
        assert rect.style.fill_color == fpdf.drawing.color_from_hex_string(fill)

    @pytest.mark.parametrize(
        "clip_path", ['clip-path="none"', 'style="clip-path: none"']
    )
    def test_svg_clip_path_none(self, clip_path):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="10" height="10" {clip_path}/></svg>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        assert svg.base_group.path_items[0].clipping_path is None

    @pytest.mark.parametrize(
        "clip_id, reference",
        [
            ("clip-1", "url(#clip-1)"),
            ("clip.a", "url(#clip.a)"),
            ("clip1", 'url("#clip1")'),
        ],
    )
    def test_svg_clip_path_reference(self, clip_id, reference):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<defs><clipPath id="clip"><rect width="1" height="1"/></clipPath>'
            f'<clipPath id="{clip_id}"><rect width="5" height="5"/></clipPath></defs>'
            f'<rect width="10" height="10" clip-path=\'{reference}\'/></svg>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        clipping_path = svg.base_group.path_items[0].clipping_path
        assert clipping_path is svg.cross_references["#" + clip_id]

    @pytest.mark.parametrize(
        "svg_body",
        [
            # as written by Adobe Illustrator
            (
                '<g><clipPath id="clip"><rect width="5" height="5"/></clipPath>'
                '<rect width="10" height="10" clip-path="url(#clip)"/></g>'
            ),
            (
                '<clipPath id="clip"><rect width="5" height="5"/></clipPath>'
                '<rect width="10" height="10" clip-path="url(#clip)"/>'
            ),
            # after the element it clips
            (
                '<rect width="10" height="10" clip-path="url(#clip)"/>'
                '<clipPath id="clip"><rect width="5" height="5"/></clipPath>'
            ),
            (
                '<rect width="10" height="10" clip-path="url(#clip)"/>'
                '<defs><clipPath id="clip"><rect width="5" height="5"/></clipPath>'
                "</defs>"
            ),
        ],
    )
    def test_svg_clip_path_outside_defs(self, svg_body, caplog):
        svg_data = f'<svg xmlns="http://www.w3.org/2000/svg">{svg_body}</svg>'
        with caplog.at_level("WARNING"):
            svg = fpdf.svg.SVGObject(svg_data)
        assert "Ignoring" not in caplog.text
        shape = svg.base_group.path_items[-1]
        while isinstance(shape, fpdf.drawing.GraphicsContext):
            shape = shape.path_items[-1]
        assert shape.clipping_path is svg.cross_references["#clip"]

    def test_svg_clip_path_with_path(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<defs><clipPath id="clip"><path d="M 0 0 H 5 V 5 H 0 Z"/></clipPath></defs>'
            '<rect width="10" height="10" clip-path="url(#clip)"/></svg>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        assert isinstance(svg.cross_references["#clip"], fpdf.drawing.ClippingPath)

    @pytest.mark.parametrize(
        "referenced",
        [
            '<rect id="SVGID_1_" width="50" height="50"/>',
            '<path id="SVGID_1_" d="M 0 0 H 50 V 50 H 0 Z"/>',
        ],
    )
    def test_svg_clip_path_with_use(self, referenced):
        # as written by Adobe Illustrator
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink"><g>'
            f"<defs>{referenced}</defs>"
            '<clipPath id="SVGID_2_"><use xlink:href="#SVGID_1_" overflow="visible"/>'
            "</clipPath>"
            '<path clip-path="url(#SVGID_2_)" d="M 0 0 L 60 60 L 0 60 Z"/></g></svg>'
        )
        svg = fpdf.svg.SVGObject(svg_data)
        clipping_path = svg.cross_references["#SVGID_2_"]
        assert isinstance(clipping_path, fpdf.drawing.ClippingPath)
        assert clipping_path.transform is None
        path = svg.base_group.path_items[0].path_items[0]
        assert path.clipping_path is clipping_path

    @pytest.mark.parametrize(
        "rect_transform, use_attributes, expected",
        [
            # translate(x, y) applies before the transform of the <use>
            (
                "",
                'x="2" y="3" transform="scale(2)"',
                fpdf.drawing.Transform.translation(2, 3)
                @ fpdf.drawing.Transform.scaling(2),
            ),
            ("", 'y="3"', fpdf.drawing.Transform.translation(0, 3)),
            # x and y are lengths, so they may have a unit
            ("", 'x="4px" y="1in"', fpdf.drawing.Transform.translation(3, 72)),
            (
                'transform="rotate(90)"',
                'x="2"',
                fpdf.drawing.Transform.rotation_d(90)
                @ fpdf.drawing.Transform.translation(2, 0),
            ),
        ],
    )
    def test_svg_clip_path_with_use_placement(
        self, rect_transform, use_attributes, expected
    ):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            f'<defs><rect id="r" width="5" height="5" {rect_transform}/>'
            f'<clipPath id="clip"><use href="#r" {use_attributes}/>'
            "</clipPath></defs></svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        assert svg.cross_references["#clip"].transform == expected

    @pytest.mark.parametrize(
        "clip_path_child, warning",
        [
            ('<use href="#missing"/>', "Ignoring <use> without a valid reference"),
            ("<use/>", "Ignoring <use> without a valid reference"),
            ('<use href="#g"/>', "Ignoring unsupported <clipPath> child tag: <g>"),
            ('<use href="#u"/>', "Ignoring unsupported <clipPath> child tag: <use>"),
            ("<text>A</text>", "Ignoring unsupported <clipPath> child tag: <text>"),
        ],
    )
    def test_svg_clip_path_unsupported_child(self, clip_path_child, warning, caplog):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<defs><g id="g"><rect width="5" height="5"/></g>'
            '<rect id="r" width="5" height="5"/><use id="u" href="#r"/>'
            f'<clipPath id="clip">{clip_path_child}</clipPath></defs></svg>'
        )
        with caplog.at_level("WARNING"):
            svg = fpdf.svg.SVGObject(svg_data)
        assert warning in caplog.text
        assert "#clip" not in svg.cross_references

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

    @pytest.mark.parametrize(
        "fill_color, stroke_color, file_suffix", parameters.svg_current_color
    )
    def test_svg_current_color(self, tmp_path, fill_color, stroke_color, file_suffix):
        svg_file = parameters.svgfile("simple_rect_current_color.svg")

        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.allow_images_transparency = False
        pdf.add_page()

        if fill_color is not None:
            pdf.set_fill_color(fill_color[0], fill_color[1], fill_color[2])
        if stroke_color is not None:
            pdf.set_draw_color(stroke_color[0], stroke_color[1], stroke_color[2])
        svg.draw_to_page(pdf)

        assert_pdf_equal(
            pdf, GENERATED_PDF_DIR / f"{svg_file.stem}{file_suffix}.pdf", tmp_path
        )

    def test_svg_render_content_in_a_tag(self, tmp_path):
        svg_file = parameters.svgfile("simple_rect_in_a_tag.svg")

        svg = fpdf.svg.SVGObject.from_file(svg_file)

        pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
        pdf.set_margin(0)
        pdf.allow_images_transparency = False
        pdf.add_page()

        svg.draw_to_page(pdf)

        assert_pdf_equal(pdf, GENERATED_PDF_DIR / f"{svg_file.stem}.pdf", tmp_path)

    def test_svg_switch_uses_the_first_unconditional_child(self):
        svg_data = """
            <svg xmlns="http://www.w3.org/2000/svg">
              <switch>
                <rect width="10" height="10" />
                <circle cx="5" cy="5" r="5" />
              </switch>
            </svg>
        """

        svg = fpdf.svg.SVGObject(svg_data)

        switch_group = svg.base_group.path_items[0]
        selected_shape = switch_group.path_items[0]
        assert isinstance(selected_shape, fpdf.drawing.PaintedPath)
        assert isinstance(
            selected_shape._root_graphics_context.path_items[1],
            fpdf.drawing.RoundedRectangle,
        )

    def test_svg_switch_skips_conditional_children_for_a_fallback(self):
        svg_data = """
            <svg xmlns="http://www.w3.org/2000/svg">
              <switch>
                <rect requiredFeatures="http://example.invalid/feature" width="10" height="10" />
                <circle cx="5" cy="5" r="5" />
              </switch>
            </svg>
        """

        svg = fpdf.svg.SVGObject(svg_data)

        switch_group = svg.base_group.path_items[0]
        selected_shape = switch_group.path_items[0]
        assert isinstance(selected_shape, fpdf.drawing.PaintedPath)
        assert isinstance(
            selected_shape._root_graphics_context.path_items[1], fpdf.drawing.Ellipse
        )

    def test_svg_rendering_image_over_page_break(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.y += 150
        pdf.image(parameters.svgfile("embedded-raster-images.svg"))
        # In the resulting document, a page break occurs before the image being rendered:
        assert_pdf_equal(
            pdf, GENERATED_PDF_DIR / "svg_rendering_image_over_page_break.pdf", tmp_path
        )

    def test_svg_text_ttf_font(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.add_font(
            family="serif", style="", fname=HERE.parent / "fonts" / "DejaVuSans.ttf"
        )
        pdf.image(
            name=HERE / "svg_sources" / "ocanada.svg",
            x=pdf.l_margin,
            y=pdf.t_margin,
            w=pdf.epw,
            h=pdf.eph,
            keep_aspect_ratio=True,
        )
        assert_pdf_equal(
            pdf,
            GENERATED_PDF_DIR / "ocanada.pdf",
            tmp_path,
        )

    @pytest.mark.parametrize(
        "text_attributes, color_operators",
        [
            ('fill="black"', "0 g"),
            ('fill="#808080" stroke="black"', "0.502 g 0 G"),
            ('style="fill:#000000;stroke:none"', "0 g"),
        ],
    )
    def test_svg_text_gray_color_in_styled_tspan(
        self, text_attributes, color_operators
    ):
        # Inkscape writes every text like this: a <tspan> with its own style
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="20">'
            f'<text x="1" y="10" {text_attributes}>'
            '<tspan style="stroke-width:0.26">Hi</tspan></text></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        assert f"{color_operators} [] 0 d BT" in bytes(pdf.output()).decode("latin-1")

    @pytest.mark.parametrize(
        "svg_body, font_sizes",
        [
            (
                (
                    '<svg xmlns="http://www.w3.org/2000/svg" style="font-size:20px">'
                    '<text y="10" style="font-size:0.8em">a</text></svg>'
                ),
                ["12"],
            ),
            (
                (
                    '<svg xmlns="http://www.w3.org/2000/svg">'
                    '<text y="10" font-size="150%">a</text></svg>'
                ),
                ["18"],
            ),
            (
                (
                    '<svg xmlns="http://www.w3.org/2000/svg" font-size="10px">'
                    '<g font-size="2em"><text y="10" font-size="0.5em">a</text></g></svg>'
                ),
                ["7.5"],
            ),
            (
                (
                    '<svg xmlns="http://www.w3.org/2000/svg"><text y="10" font-size="20px">'
                    'a<tspan font-size="2ex">b</tspan></text></svg>'
                ),
                ["15", "15"],
            ),
            (
                (
                    '<svg xmlns="http://www.w3.org/2000/svg">'
                    '<g style="font-size:2em"><text y="10">a</text></g></svg>'
                ),
                ["24"],
            ),
        ],
    )
    def test_svg_relative_font_size(self, svg_body, font_sizes):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        fpdf.svg.SVGObject(svg_body).draw_to_page(pdf)
        output = bytes(pdf.output()).decode("latin-1")
        assert re.findall(r"/F\d+ ([\d.]+) Tf", output) == font_sizes

    @pytest.mark.parametrize(
        "pattern_content, font_sizes",
        [
            ('<rect width="5" height="5"/>', []),
            ('<text y="5" font-size="0.5em">a</text>', [b"6"]),
        ],
    )
    def test_svg_relative_font_size_in_pattern(self, pattern_content, font_sizes):
        # the ancestors of a <pattern> give its contents their font size too
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
            'font-size="2em"><defs><g font-size="50%"><pattern id="p" width="10" '
            f'height="10" patternUnits="userSpaceOnUse">{pattern_content}</pattern>'
            '</g></defs><rect width="100" height="100" fill="url(#p)"/></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.add_page()
        svg.draw_to_page(pdf)
        output = bytes(pdf.output())
        streams = re.findall(
            rb"/FlateDecode.*?stream\r?\n(.*?)\r?\nendstream", output, re.S
        )
        contents = b"".join(zlib.decompress(stream) for stream in streams)
        assert re.findall(rb"/F\d+ ([\d.]+) Tf", contents) == font_sizes

    @pytest.mark.parametrize(
        "hidden_rect",
        [
            '<rect width="10" height="10" display="none"/>',
            # a hidden Inkscape layer
            '<g style="display:none"><rect width="10" height="10"/></g>',
            (
                "<style>.hidden { display: none }</style>"
                '<rect class="hidden" width="10" height="10"/>'
            ),
        ],
    )
    def test_svg_display_none(self, hidden_rect):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            f'{hidden_rect}<circle cx="25" cy="25" r="3"/></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        output = bytes(pdf.output()).decode("latin-1")
        assert " re " not in output  # the rectangle
        assert " c " in output  # the circle

    def test_svg_use_position_with_units(self):
        """The x and y of a <use> are lengths, so they may have a unit."""
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<defs><rect id="square" width="10" height="10"/></defs>'
            '<use href="#square" x="20px" y="1in"/></svg>'
        )
        use = svg.base_group.path_items[0]
        assert use.transform == fpdf.drawing.Transform.translation(15, 72)

    def test_svg_display_none_referenced(self):
        """An element in a hidden group can still be drawn by a <use>."""
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<g display="none"><rect id="square" width="10" height="10"/></g>'
            '<use href="#square" x="20"/></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        output = bytes(pdf.output()).decode("latin-1")
        assert output.count(" re ") == 1

    @pytest.mark.parametrize(
        "svg_data",
        [
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" '
                'display="none"><rect width="10" height="10"/></svg>'
            ),
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
                '<rect id="square" width="10" height="10" display="none"/>'
                '<use href="#square" x="20"/></svg>'
            ),
            (
                '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
                '<defs><rect id="square" width="10" height="10" display="none"/>'
                '</defs><use href="#square" x="20"/></svg>'
            ),
        ],
    )
    def test_svg_display_none_nothing_drawn(self, svg_data):
        """A hidden <svg>, or a <use> of an element that is itself hidden."""
        svg = fpdf.svg.SVGObject(svg_data)
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        assert " re " not in bytes(pdf.output()).decode("latin-1")

    def test_svg_display_none_tspan(self):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<text x="1" y="10">ab<tspan display="none">cd</tspan>ef</text></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        output = bytes(pdf.output()).decode("latin-1")
        assert "(ab) Tj" in output
        assert "(ef) Tj" in output
        assert "cd" not in output

    @pytest.mark.parametrize(
        "declaration, file_encoding, from_file_kwargs",
        [
            ('<?xml version="1.0" encoding="iso-8859-1"?>', "latin-1", {}),
            ("", "utf-8", {}),
            ("", "latin-1", {"encoding": "latin-1"}),
        ],
    )
    def test_svg_from_file_encoding(
        self, tmp_path, declaration, file_encoding, from_file_kwargs
    ):
        svg_path = tmp_path / "text.svg"
        svg_path.write_bytes(
            (
                f'{declaration}<svg xmlns="http://www.w3.org/2000/svg" width="50" '
                'height="20"><text x="1" y="10" font-family="helvetica">Z\u00fcrich'
                "</text></svg>"
            ).encode(file_encoding)
        )
        svg = fpdf.svg.SVGObject.from_file(svg_path, **from_file_kwargs)
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        svg.draw_to_page(pdf)
        assert "(Z\u00fcrich) Tj" in bytes(pdf.output()).decode("latin-1")

    @pytest.mark.parametrize("text", ["a \u2013 b", "price: \u20ac5", "\u2192 next"])
    def test_svg_text_core_font_unsupported_character(self, text):
        svg = fpdf.svg.SVGObject(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="20">'
            f'<text x="1" y="10" font-family="helvetica">{text}</text></svg>'
        )
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("helvetica")
        # The same error as for text written with cell()
        with pytest.raises(fpdf.errors.FPDFUnicodeEncodingException) as cell_error:
            pdf.cell(text=text)
        with pytest.raises(fpdf.errors.FPDFUnicodeEncodingException) as svg_error:
            svg.draw_to_page(pdf)
        assert str(svg_error.value) == str(cell_error.value)

    def test_svg_symbol(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">'
            "<defs>"
            '<symbol id="rond" width="10" height="10" viewBox="0 0 2 2"><circle cx="1" cy="1" r="1" fill="red"/></symbol>'
            "</defs>"
            '<use href="#rond" x="10" y="10" width="40" height="40"/>'
            "</svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        assert svg is not None
        assert "#rond" in svg.cross_references

    def test_svg_symbol_uses_symbol_dimensions(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20">'
            '<symbol id="myDot" width="10" height="10" viewBox="0 0 2 2">'
            '<circle cx="1" cy="1" r="1" />'
            "</symbol>"
            '<use href="#myDot" x="5" y="5" />'
            "</svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        symbol_use = svg.base_group.path_items[0]
        assert tuple(symbol_use.transform) == pytest.approx((10, 0, 0, 10, 5, 5))
        assert tuple(symbol_use.path_items[0].transform) == pytest.approx(
            (0.5, 0, 0, 0.5, 0, 0)
        )

    def test_svg_symbol_use_dimensions_override_symbol_dimensions(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20">'
            '<symbol id="myDot" width="10" height="10" viewBox="0 0 2 2">'
            '<circle cx="1" cy="1" r="1" />'
            "</symbol>"
            '<use href="#myDot" x="5" y="5" width="40" height="20" />'
            "</svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        symbol_use = svg.base_group.path_items[0]
        assert tuple(symbol_use.transform) == pytest.approx((40, 0, 0, 20, 5, 5))

    @pytest.mark.parametrize("viewbox", ["0 0 nan 2", "0 0 2 inf"])
    def test_svg_symbol_not_finite_viewbox(self, viewbox):
        with pytest.raises(ValueError, match="invalid viewBox"):
            fpdf.svg.SVGObject(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20">'
                f'<symbol id="myDot" width="10" height="10" viewBox="{viewbox}">'
                '<circle cx="1" cy="1" r="1"/></symbol>'
                '<use href="#myDot" x="5" y="5"/></svg>'
            )

    def test_svg_symbol_viewbox_origin_is_translated_before_scaling(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20">'
            '<symbol id="myDot" width="10" height="10" viewBox="10 10 2 2">'
            '<circle cx="11" cy="11" r="1" />'
            "</symbol>"
            '<use href="#myDot" x="5" y="5" />'
            "</svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        symbol_use = svg.base_group.path_items[0]
        assert tuple(symbol_use.transform) == pytest.approx((10, 0, 0, 10, 5, 5))
        assert tuple(symbol_use.path_items[0].transform) == pytest.approx(
            (0.5, 0, 0, 0.5, -5, -5)
        )

    def test_use_width_height_do_not_scale_non_symbol_references(self):
        svg_data = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 20">'
            '<defs><path id="path" d="M 0 0 L 1 2 Z"/></defs>'
            '<use href="#path" x="5" y="5" width="40" height="20" />'
            "</svg>"
        )
        svg = fpdf.svg.SVGObject(svg_data)
        path_use = svg.base_group.path_items[0]
        assert tuple(path_use.transform) == pytest.approx((1, 0, 0, 1, 5, 5))


def test_user_space_gradient_tracks_svg_image_transform(tmp_path):
    svg_data = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
            <defs>
            <linearGradient id="g" x1="5" y1="5" x2="45" y2="45" gradientUnits="userSpaceOnUse">
                <stop offset="0" stop-color="#ff0000" />
                <stop offset="1" stop-color="#0000ff" />
            </linearGradient>
            </defs>
            <rect width="50" height="50" fill="url(#g)" />
        </svg>
        """
    pdf = fpdf.FPDF(unit="mm", format=(180, 70))
    pdf.set_margin(0)
    pdf.add_page()

    pdf.image(BytesIO(svg_data.encode()), x=10, y=10)

    pdf.image(BytesIO(svg_data.encode()), x=95, y=10)

    assert_pdf_equal(
        pdf,
        GENERATED_PDF_DIR / "gradient_user_space_tracks_svg_transform.pdf",
        tmp_path,
    )


@pytest.mark.parametrize(
    "shape, converted",
    [
        ('<circle cx="1in" cy="2in" r="0.5in"/>', '<circle cx="72" cy="144" r="36"/>'),
        (
            '<ellipse cx="1in" cy="2in" rx="0.5in" ry="1in"/>',
            '<ellipse cx="72" cy="144" rx="36" ry="72"/>',
        ),
        ('<ellipse rx="0.5in"/>', '<ellipse rx="36"/>'),
        ('<ellipse ry="0.5in"/>', '<ellipse ry="36"/>'),
        (
            '<line x1="1in" y1="2in" x2="3in" y2="4in"/>',
            '<line x1="72" y1="144" x2="216" y2="288"/>',
        ),
        (
            '<rect width="4in" height="4in" rx="1in" ry="2in"/>',
            '<rect width="288" height="288" rx="72" ry="144"/>',
        ),
        (
            '<rect width="4in" height="4in" rx="1in"/>',
            '<rect width="288" height="288" rx="72"/>',
        ),
        (
            '<rect width="4in" height="4in" ry="1in"/>',
            '<rect width="288" height="288" ry="72"/>',
        ),
    ],
)
def test_svg_shape_absolute_lengths(shape, converted):
    xml = parse_xml_str(shape)
    converter = getattr(fpdf.svg.ShapeBuilder, xml.tag)
    actual = converter(xml)
    expected = converter(parse_xml_str(converted))
    assert (
        actual._root_graphics_context.path_items
        == expected._root_graphics_context.path_items
    )


TINY_PNG_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAMFBMVEU0OkArMjhobHEoPUP"
    "FEBIuO0L+AAC2FBZ2JyuNICOfGx7xAwTjCAlCNTvVDA1aLzQ3COjMAAAAVUlEQVQI12NgwAaCDSA0888GCItjn0szWGBJ"
    "TVoGSCjWs8TleQCQYV95evdxkFT8Kpe0PLDi5WfKd4LUsN5zS1sKFolt8bwAZrCaGqNYJAgFDEpQAAAzmxafI4vZWwAAA"
    "ABJRU5ErkJggg=="
)


@pytest.mark.parametrize(
    "aspect_ratio_attr, expected_w, expected_h",
    [
        ('preserveAspectRatio="none"', 100.0, 50.0),
        ('preserveAspectRatio="defer none"', 100.0, 50.0),
        ('preserveAspectRatio="xMidYMid meet"', 50.0, 50.0),
        ("", 50.0, 50.0),
    ],
)
def test_svg_image_preserve_aspect_ratio(
    aspect_ratio_attr, expected_w, expected_h, caplog
):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="100" height="50" {aspect_ratio_attr}/>'
        "</svg>"
    )
    with caplog.at_level("WARNING"):
        pdf.image(BytesIO(svg.encode()))
    assert "not supported" not in caplog.text
    content = pdf.pages[1].contents.decode("latin1")
    expected_chunk = f"{expected_w:.2f} 0 0 -{expected_h:.2f}"
    assert expected_chunk in content


@pytest.mark.parametrize(
    "unit, scale",
    [("", 1.0), ("px", 0.75), ("pt", 1.0), ("mm", 72 / 25.4)],
)
def test_svg_image_length_units(unit, scale):
    # as in the logo of narwhals, which gives every length of its <image> in px
    svg = fpdf.svg.SVGObject(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10{unit}" y="20{unit}" '
        f'width="40{unit}" height="30{unit}"/></svg>'
    )
    image = svg.base_group.path_items[0]
    assert (image.x, image.y, image.width, image.height) == pytest.approx(
        (10 * scale, 20 * scale, 40 * scale, 30 * scale)
    )


def test_svg_image_transform(caplog):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="40" height="40" transform="translate(15, 25)"/>'
        "</svg>"
    )
    with caplog.at_level("WARNING"):
        pdf.image(BytesIO(svg.encode()))
    assert "not supported" not in caplog.text
    content = pdf.pages[1].contents.decode("latin1")
    assert "1 0 0 1 15 25 cm" in content


@pytest.mark.parametrize(
    "style_attr",
    [
        'opacity="0.5"',
        'style="opacity: 0.5"',
    ],
)
def test_svg_image_opacity_and_style(style_attr, caplog):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="40" height="40" {style_attr}/>'
        "</svg>"
    )
    with caplog.at_level("WARNING"):
        pdf.image(BytesIO(svg.encode()))
    assert "not supported" not in caplog.text
    content = bytes(pdf.pages[1].contents)
    assert b"gs" in content
    pdf_bytes = bytes(pdf.output())
    assert b"/ca 0.5" in pdf_bytes or b"/ca .5" in pdf_bytes


@pytest.mark.parametrize(
    "aspect_ratio_attr",
    [
        'preserveAspectRatio="xMinYMin meet"',
        'preserveAspectRatio="xMidYMid slice"',
        'preserveAspectRatio="xMinYMin slice"',
        'preserveAspectRatio="defer xMinYMin meet"',
    ],
)
def test_svg_image_preserve_aspect_ratio_unsupported_mode_warning(
    aspect_ratio_attr, caplog
):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="100" height="50" {aspect_ratio_attr}/>'
        "</svg>"
    )
    with caplog.at_level("WARNING"):
        pdf.image(BytesIO(svg.encode()))
    assert "alignment/slice mode" in caplog.text
    content = pdf.pages[1].contents.decode("latin1")
    assert "50.00 0 0 -50.00" in content


@pytest.mark.parametrize(
    "attributes",
    [
        'style="fill-opacity: 0"',
        'style="stroke-opacity: 0"',
        'style="fill-opacity: 0; stroke-opacity: 0; fill: red; stroke: blue"',
        'fill-opacity="0"',
        'stroke-opacity="0"',
        'style="fill-opacity: 0" transform="translate(10, 20)"',
    ],
)
def test_svg_image_ignores_fill_and_stroke_opacity(attributes):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="40" height="40" {attributes}/>'
        "</svg>"
    )
    pdf.image(BytesIO(svg.encode()))
    pdf_bytes = bytes(pdf.output())
    assert (
        b"/ca 0\n" not in pdf_bytes
        and b"/ca 0.0" not in pdf_bytes
        and b"/ca 0 " not in pdf_bytes
    )


@pytest.mark.parametrize(
    "attributes",
    [
        'style="fill-opacity: 0; opacity: 0.5"',
        'opacity="0.5" fill-opacity="0"',
    ],
)
def test_svg_image_opacity_with_fill_opacity_override(attributes):
    pdf = fpdf.FPDF()
    pdf.add_page()
    svg = (
        '<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">'
        f'<image href="{TINY_PNG_DATA_URI}" x="10" y="20" width="40" height="40" {attributes}/>'
        "</svg>"
    )
    pdf.image(BytesIO(svg.encode()))
    pdf_bytes = bytes(pdf.output())
    assert b"/ca 0.5" in pdf_bytes or b"/ca .5" in pdf_bytes
    assert b"/ca 0\n" not in pdf_bytes and b"/ca 0.0" not in pdf_bytes
