from pathlib import Path

from fpdf import FPDF, ViewerPreferences
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_default_viewer_preferences(tmp_path):
    pdf = FPDF()
    pdf.viewer_preferences = ViewerPreferences()
    pdf.set_font("helvetica", size=30)
    pdf.add_page()
    pdf.cell(txt="page 1")
    pdf.add_page()
    pdf.cell(txt="page 2")
    assert_pdf_equal(pdf, HERE / "default_viewer_preferences.pdf", tmp_path)


def test_custom_viewer_preferences(tmp_path):
    pdf = FPDF()
    pdf.viewer_preferences = ViewerPreferences(
        hide_toolbar=True,
        hide_menubar=True,
        hide_window_u_i=True,
        fit_window=True,
        center_window=True,
        display_doc_title=True,
        non_full_screen_page_mode="USE_OUTLINES",
    )
    pdf.set_font("helvetica", size=30)
    pdf.add_page()
    pdf.cell(txt="page 1")
    pdf.add_page()
    pdf.cell(txt="page 2")
    assert_pdf_equal(pdf, HERE / "custom_viewer_preferences.pdf", tmp_path)
