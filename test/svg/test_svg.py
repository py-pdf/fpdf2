# pylint: disable=redefined-outer-name, no-self-use, protected-access
from pathlib import Path

import fpdf
from ..conftest import assert_pdf_equal

import pytest


from . import parameters

GENERATED_PDF_DIR = Path(__file__).resolve().parent / "generated_pdf"


def svg_snippet(snippet):
    return f"""
        <?xml version="1.0" standalone="no"?>
        <svg width="4cm" height="4cm" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" version="1.1">
        {snippet}
        </svg>
        """


class TestUnits:
    @pytest.mark.parametrize(
        "name", [pytest.param(name, id=name) for name in fpdf.svg.relative_length_units]
    )
    def test_resolve_bad_length_units(self, name):
        with pytest.raises(ValueError):
            fpdf.svg.resolve_length(f" 1{name}")

    @pytest.mark.parametrize(
        "name", [pytest.param(name, id=name) for name in fpdf.svg.absolute_length_units]
    )
    def test_resolve_good_length_units(self, name):
        computed = fpdf.svg.resolve_length(f"  1 {name} ")
        assert isinstance(computed, float)

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


class TestSVGPathParsing:
    @pytest.mark.parametrize("path, result", parameters.svg_path_directives)
    def test_parsing_all_directives(self, path, result):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        assert result == pdf_path._root_graphics_context.path_items

    @pytest.mark.parametrize("path, result", parameters.svg_path_edge_cases)
    def test_parsing_edge_cases(self, path, result):
        pdf_path = fpdf.drawing.PaintedPath()

        fpdf.svg.svg_path_converter(pdf_path, path)

        assert result == pdf_path._root_graphics_context.path_items


@pytest.mark.parametrize("svg_file", parameters.test_svg_sources)
def test_svg_conversion(tmp_path, svg_file):
    svg = fpdf.svg.SVGObject.from_file(svg_file)

    pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
    pdf.add_page()

    svg.draw_to_page(pdf)

    assert_pdf_equal(pdf, GENERATED_PDF_DIR / f"{svg_file.stem}.pdf", tmp_path)
