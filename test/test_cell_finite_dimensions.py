# pylint: disable=no-member
from io import BytesIO

import pytest
from pypdf import PdfReader

from fpdf import FPDF

NON_FINITE_VALUES = (float("nan"), float("inf"), float("-inf"))


def _new_pdf() -> FPDF:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    return pdf


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_cell_rejects_non_finite_width(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.cell(w=value, h=10, text="a")


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_cell_rejects_non_finite_height(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.cell(w=10, h=value, text="a")


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_multi_cell_rejects_non_finite_width(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.multi_cell(w=value, h=10, text="a")


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_multi_cell_rejects_non_finite_height(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.multi_cell(w=10, h=value, text="a")


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_multi_cell_dry_run_rejects_non_finite_width(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.multi_cell(w=value, h=10, text="a", dry_run=True)


@pytest.mark.parametrize("value", NON_FINITE_VALUES)
def test_write_rejects_non_finite_height(value):
    pdf = _new_pdf()
    with pytest.raises(ValueError, match="finite"):
        pdf.write(h=value, text="a")


@pytest.mark.parametrize(
    "call",
    (
        lambda pdf: pdf.cell(w=10, h=10, text="a"),
        lambda pdf: pdf.cell(w=0, h=10, text="a"),
        lambda pdf: pdf.cell(text="a"),  # w and h default to None
        lambda pdf: pdf.multi_cell(w=10, h=10, text="a"),
        lambda pdf: pdf.multi_cell(w=0, h=10, text="a"),
        lambda pdf: pdf.multi_cell(w=10, text="a"),  # h defaults to the font size
        lambda pdf: pdf.write(h=10, text="a"),
        lambda pdf: pdf.write(text="a"),  # h defaults to the current font size
    ),
)
def test_finite_and_default_dimensions_still_render(call):
    pdf = _new_pdf()
    call(pdf)

    content = PdfReader(BytesIO(pdf.output())).pages[0].get_contents().get_data()
    assert b"nan" not in content and b"inf" not in content
