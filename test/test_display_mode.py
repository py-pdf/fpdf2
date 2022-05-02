from pathlib import Path

import pytest

from fpdf import FPDF
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
        fill=False,
        link="",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.set_display_mode(zoom=zoom)
    assert_pdf_equal(doc, HERE / f"zoom-{zoom}.pdf", tmp_path)


@pytest.mark.parametrize("layout", ["single", "continuous", "two", "default"])
def test_setting_all_layout(layout, tmp_path):
    """This test executes some possible inputs to FPDF#set_display_mode."""
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(
        w=72,
        h=0,
        border=1,
        txt="hello world",
        fill=False,
        link="",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.set_display_mode(zoom="default", layout=layout)
    assert_pdf_equal(doc, HERE / f"layout-{layout}.pdf", tmp_path)
