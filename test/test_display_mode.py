from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize("zoom_input", ["fullpage", "fullwidth", "real", "default"])
def test_setting_all_zoom(zoom_input, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=False, link="")
    doc.set_display_mode(zoom=zoom_input, layout="continuous")
    assert_pdf_equal(doc, HERE / f"catalog-zoom-{zoom_input}.pdf", tmp_path)


@pytest.mark.parametrize("layout_input", ["single", "continuous", "two"])
def test_setting_all_layout(layout_input, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=False, link="")
    doc.set_display_mode(zoom="default", layout=layout_input)
    assert_pdf_equal(doc, HERE / f"catalog-layout-{layout_input}.pdf", tmp_path)
