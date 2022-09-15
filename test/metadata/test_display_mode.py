from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.errors import FPDFException
from fpdf.enums import PageLayout, PageMode
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize("zoom", ["fullpage", "fullwidth", "real", "default"])
def test_setting_all_zoom(zoom, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(
        w=72,
        h=0,
        border=1,
        txt="hello world",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.set_display_mode(zoom=zoom)
    assert_pdf_equal(doc, HERE / f"zoom-{zoom}.pdf", tmp_path)


def test_setting_zoom_raises_correct_error():
    doc = FPDF()
    with pytest.raises(FPDFException):
        doc.set_display_mode("foo")


@pytest.mark.parametrize("page_layout", PageLayout.__members__.keys())
def test_page_layout(page_layout, tmp_path):
    pdf = FPDF()
    pdf.set_display_mode(zoom="default", layout=page_layout)
    pdf.set_font("helvetica", size=30)
    pdf.add_page()
    pdf.cell(txt="page 1")
    pdf.add_page()
    pdf.cell(txt="page 2")
    assert_pdf_equal(pdf, HERE / f"page-layout-{page_layout}.pdf", tmp_path)


@pytest.mark.parametrize("layout_alias", ["single", "continuous", "two", "default"])
def test_layout_aliases(layout_alias, tmp_path):
    pdf = FPDF()
    pdf.set_display_mode(zoom="default", layout=layout_alias)
    pdf.set_font("helvetica", size=30)
    pdf.add_page()
    pdf.cell(txt="page 1")
    pdf.add_page()
    pdf.cell(txt="page 2")
    assert_pdf_equal(pdf, HERE / f"layout-alias-{layout_alias}.pdf", tmp_path)


@pytest.mark.parametrize("page_mode", PageMode.__members__.keys())
def test_page_mode(page_mode, tmp_path):
    pdf = FPDF()
    pdf.page_mode = page_mode
    pdf.set_font("helvetica", size=30)
    pdf.add_page()
    pdf.cell(txt="page 1")
    pdf.add_page()
    pdf.cell(txt="page 2")
    assert_pdf_equal(pdf, HERE / f"page-mode-{page_mode}.pdf", tmp_path)
