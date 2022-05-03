from pathlib import Path

import fpdf
from fpdf.errors import FPDFException
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent
POLYLINE_COORDINATES = [(10, 10), (40, 10), (10, 40)]
SCALING_FACTORS_FOR_UNITS = [
    ("pt", 1),
    ("mm", 1 / (72 / 25.4)),
    ("cm", 1 / (72 / 2.54)),
    ("in", 1 / 72),
]


@pytest.mark.parametrize("unit, factor", SCALING_FACTORS_FOR_UNITS)
def test_polyline_command_all_k(unit, factor):
    pdf = fpdf.FPDF(unit=unit)
    pdf.add_page()
    data = []
    # pylint: disable=protected-access
    pdf._out = data.append

    pdf.polyline(scale_points(POLYLINE_COORDINATES, factor))
    assert "".join(data) == "10.00 831.89 m40.00 831.89 l10.00 801.89 l S"
    data.clear()

    pdf.polyline(scale_points(POLYLINE_COORDINATES, factor), fill=True)
    assert "".join(data) == "10.00 831.89 m40.00 831.89 l10.00 801.89 l B"
    data.clear()

    pdf.polyline(scale_points(POLYLINE_COORDINATES, factor), polygon=True)
    assert "".join(data) == "10.00 831.89 m40.00 831.89 l10.00 801.89 l h S"
    data.clear()

    pdf.polyline(scale_points(POLYLINE_COORDINATES, factor), polygon=True, fill=True)
    assert "".join(data) == "10.00 831.89 m40.00 831.89 l10.00 801.89 l h B"


def scale_points(raw_points, k_recip):
    return [(k_recip * coord[0], k_recip * coord[1]) for coord in raw_points]


def test_check_page():
    pdf = fpdf.FPDF(unit="pt")

    with pytest.raises(FPDFException) as polyline_no_page:
        pdf.polyline(POLYLINE_COORDINATES)
    expected_error_msg = "No page open, you need to call add_page() first"
    assert expected_error_msg == str(polyline_no_page.value)

    with pytest.raises(FPDFException) as polygon_no_page:
        pdf.polygon(POLYLINE_COORDINATES)
    assert expected_error_msg == str(polygon_no_page.value)


def test_filled_polygon(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_line_width(2)
    pdf.set_fill_color(r=255, g=0, b=0)
    coords = ((100, 0), (5, 69), (41, 181), (159, 181), (195, 69))
    pdf.polygon(coords, fill=True)
    assert_pdf_equal(pdf, HERE / "filled_polygon.pdf", tmp_path)
