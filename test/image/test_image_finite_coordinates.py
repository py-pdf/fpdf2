from pathlib import Path

import pytest

from fpdf import FPDF

HERE = Path(__file__).resolve().parent
PNG = HERE / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"x": float("nan")},
        {"y": float("nan")},
        {"w": float("nan")},
        {"h": float("inf")},
        {"x": float("inf")},
    ],
)
def test_non_finite_image_coordinates_raise(kwargs):
    pdf = FPDF()
    pdf.add_page()

    params = {"w": 10, "h": 10}
    params.update(kwargs)

    with pytest.raises(ValueError, match="finite"):
        pdf.image(PNG, **params)


def test_valid_image_coordinates_still_work(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(PNG, x=10, y=10, w=10, h=10)

    output = tmp_path / "out.pdf"
    pdf.output(output)
    assert output.stat().st_size > 0
