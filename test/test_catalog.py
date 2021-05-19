from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def document_operations(doc):
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=False, link="")


@pytest.mark.parametrize("zoom_input", ["fullpage", "fullwidth", "real", "default"])
def test_setting_all_zoom(zoom_input, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = fpdf.FPDF()
    document_operations(doc)
    doc.set_display_mode(zoom=zoom_input, layout="continuous")
    assert_pdf_equal(doc, HERE / f"catalog-zoom-{zoom_input}.pdf", tmp_path)


@pytest.mark.parametrize("layout_input", ["single", "continuous", "two"])
def test_setting_all_layout(layout_input, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = fpdf.FPDF()
    document_operations(doc)
    doc.set_display_mode(zoom="default", layout=layout_input)
    assert_pdf_equal(doc, HERE / f"catalog-layout-{layout_input}.pdf", tmp_path)


def test_add_page_format(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    for i in range(9):
        pdf.add_page(format=(210 * (1 - i / 10), 297 * (1 - i / 10)))
        pdf.cell(w=10, h=10, txt=str(i))
    pdf.add_page(same=True)
    pdf.cell(w=10, h=10, txt="9")
    assert_pdf_equal(pdf, HERE / "add_page_format.pdf", tmp_path)
