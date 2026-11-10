import fpdf
import pytest


@pytest.mark.parametrize(
    "draw",
    (
        lambda pdf: pdf.bezier(((10, 10), (20, float("nan")), (30, 30))),
        lambda pdf: pdf.bezier(((10, 10), (20, 20), (30, float("inf")), (40, 40))),
    ),
    ids=("quadratic", "cubic"),
)
def test_non_finite_bezier_coordinates_raise(draw):
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(ValueError, match="finite"):
        draw(pdf)
