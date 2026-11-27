import pytest

from fpdf import FPDF


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("rect_clip", {"x": float("nan"), "y": 10, "w": 10, "h": 10}),
        ("rect_clip", {"x": 10, "y": float("nan"), "w": 10, "h": 10}),
        ("rect_clip", {"x": 10, "y": 10, "w": float("nan"), "h": 10}),
        ("rect_clip", {"x": 10, "y": 10, "w": 10, "h": float("inf")}),
        ("elliptic_clip", {"x": float("nan"), "y": 10, "w": 10, "h": 10}),
        ("elliptic_clip", {"x": 10, "y": float("nan"), "w": 10, "h": 10}),
        ("elliptic_clip", {"x": 10, "y": 10, "w": float("nan"), "h": 10}),
        ("elliptic_clip", {"x": 10, "y": 10, "w": 10, "h": float("inf")}),
        ("round_clip", {"x": float("nan"), "y": 10, "r": 10}),
        ("round_clip", {"x": 10, "y": float("nan"), "r": 10}),
        ("round_clip", {"x": 10, "y": 10, "r": float("inf")}),
    ],
)
def test_non_finite_clip_coordinates_raise(method, kwargs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    with pytest.raises(ValueError, match="finite"):
        with getattr(pdf, method)(**kwargs):
            pass


def test_valid_clip_coordinates_still_work(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    with pdf.rect_clip(x=10, y=10, w=50, h=50):
        pdf.cell(10, 10, "x")
    with pdf.elliptic_clip(x=10, y=10, w=50, h=50):
        pdf.cell(10, 10, "x")
    with pdf.round_clip(x=10, y=10, r=25):
        pdf.cell(10, 10, "x")

    output = tmp_path / "out.pdf"
    pdf.output(output)
    assert output.stat().st_size > 0
