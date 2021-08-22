from pathlib import Path
import re

import fpdf
from test.conftest import assert_pdf_equal

import pytest


HERE = Path(__file__).resolve().parent


@pytest.fixture(
    params=[
        "arcs01.svg",
        "arcs02.svg",
        "circle01.svg",
        "cubic01.svg",
        "cubic02.svg",
        "ellipse01.svg",
        "line01.svg",
        "polygon01.svg",
        "polyline01.svg",
        "quad01.svg",
        "rect01.svg",
        "rect02.svg",
        "triangle01.svg",
        "SVG_logo.svg",
    ],
    ids=lambda param: param,
)
def svg_file(request):
    return HERE / "svg_sources" / request.param


def test_svg_conversion(tmp_path, svg_file):
    svg = fpdf.svg.SVGObject.from_file(svg_file)

    pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
    pdf.add_page()

    svg.draw_to_page(pdf)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / f"{svg_file.stem}.pdf", tmp_path)
