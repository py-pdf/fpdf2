"""Test for round corners rendering - including thick borders and fill artifacts"""

from pathlib import Path
import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_round_corners_thick_border(tmp_path):
    """Test that thick borders work correctly with rounded corners."""
    pdf = fpdf.FPDF()
    pdf.add_page()

    # Thick border test - should have smooth, consistent corners
    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_line_width(6)
    pdf.rect(50, 40, 120, 70, style="DF", round_corners=True, corner_radius=12)

    assert_pdf_equal(pdf, HERE / "round_corners_thick_border.pdf", tmp_path)


def test_round_corners_fill_no_artifacts(tmp_path):
    """Test that filled rounded corners don't show line artifacts."""
    pdf = fpdf.FPDF()
    pdf.add_page()

    # Fill with background color - should have no visible lines at corners
    pdf.set_fill_color(230, 120, 125)
    pdf.set_line_width(1)
    pdf.rect(50, 40, 120, 70, style="DF", round_corners=True, corner_radius=12)

    assert_pdf_equal(pdf, HERE / "round_corners_fill_no_artifacts.pdf", tmp_path)


def test_round_corners_combined_issue(tmp_path):
    """Test both issues together."""
    pdf = fpdf.FPDF()
    pdf.add_page()

    # Issue 1: Thick border
    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_line_width(6)
    pdf.rect(50, 40, 120, 70, style="DF", round_corners=True, corner_radius=12)

    # Issue 2: Fill artifacts
    pdf.set_fill_color(230, 120, 125)
    pdf.set_line_width(1)
    pdf.rect(50, 160, 120, 70, style="DF", round_corners=True, corner_radius=12)

    assert_pdf_equal(pdf, HERE / "round_corners_combined_fix.pdf", tmp_path)


def test_round_corners_draw_only(tmp_path):
    """Test rounded corners with draw only (no fill)."""
    pdf = fpdf.FPDF()
    pdf.add_page()

    # Draw only - should have smooth rounded corners
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(2)
    pdf.rect(50, 40, 120, 70, style="D", round_corners=True, corner_radius=12)

    assert_pdf_equal(pdf, HERE / "round_corners_draw_only.pdf", tmp_path)


def test_round_corners_fill_only(tmp_path):
    """Test rounded corners with fill only (no border)."""
    pdf = fpdf.FPDF()
    pdf.add_page()

    # Fill only - should have smooth rounded corners without border
    pdf.set_fill_color(100, 150, 200)
    pdf.rect(50, 40, 120, 70, style="F", round_corners=True, corner_radius=12)

    assert_pdf_equal(pdf, HERE / "round_corners_fill_only.pdf", tmp_path)
