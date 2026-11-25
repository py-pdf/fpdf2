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
        lambda pdf: pdf.rect(10, 10, float("nan"), 20),
        lambda pdf: pdf.rect(10, 10, 20, float("inf")),
        lambda pdf: pdf.rect(float("inf"), 10, 20, 20),
        lambda pdf: pdf.rect(10, float("nan"), 20, 20),
        lambda pdf: pdf.arc(float("nan"), 10, 20, 0, 90),
        lambda pdf: pdf.arc(10, float("inf"), 20, 0, 90),
        lambda pdf: pdf.solid_arc(float("nan"), 10, 20, 0, 90),
    ),
    ids=(
        "line",
        "polyline",
        "polygon",
        "ellipse",
        "circle",
        "rect-w",
        "rect-h",
        "rect-x",
        "rect-y",
        "arc-x",
        "arc-y",
        "solid-arc-x",
    ),
)
def test_non_finite_drawing_coordinates_raise(draw):
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ValueError, match="finite"):
        draw(pdf)
