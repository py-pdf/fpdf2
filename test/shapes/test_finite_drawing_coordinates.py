import fpdf
import pytest


@pytest.mark.parametrize(
    "draw",
    (
        lambda pdf: pdf.line(10, 10, 20, float("inf")),
        lambda pdf: pdf.polyline(((10, 10), (20, float("inf")))),
        lambda pdf: pdf.polygon(((10, 10), (20, float("nan")))),
        lambda pdf: pdf.ellipse(10, 10, 20, float("inf")),
        lambda pdf: pdf.circle(10, 10, float("nan")),
    ),
    ids=("line", "polyline", "polygon", "ellipse", "circle"),
)
def test_non_finite_drawing_coordinates_raise(draw):
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ValueError, match="finite"):
        draw(pdf)
