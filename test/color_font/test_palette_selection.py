"""
Unit tests for color font palette selection feature.
Tests the palette parameter in add_font() method.
"""

from pathlib import Path
from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_palette_parameter_acceptance(tmp_path):
    """Test that the palette parameter is accepted and stored."""
    pdf = FPDF()

    # Test that palette parameter is accepted without error
    pdf.add_font("Nabla", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=0)

    # Test that we can add the font multiple times with different palettes
    pdf.add_font("Nabla-P1", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=1)
    pdf.add_font("Nabla-P2", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=2)

    # Test that we can use these fonts
    pdf.add_page()
    pdf.set_font("Nabla", size=24)
    pdf.cell(text="HELLO")

    pdf.set_font("Nabla-P1", size=24)
    pdf.cell(text="WORLD")

    pdf.set_font("Nabla-P2", size=24)
    pdf.cell(text="TEST")

    assert_pdf_equal(pdf, HERE / "palette_parameter_acceptance.pdf", tmp_path)


def test_palette_defaults(tmp_path):
    """Test that palette defaults work correctly."""
    pdf = FPDF()

    # Test default palette (None should become 0)
    pdf.add_font("Nabla-Default", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf")

    # Test explicit palette 0
    pdf.add_font("Nabla-Explicit", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=0)

    # Both should work the same way
    pdf.add_page()
    pdf.set_font("Nabla-Default", size=24)
    pdf.cell(text="DEFAULT")

    pdf.set_font("Nabla-Explicit", size=24)
    pdf.cell(text="EXPLICIT")

    assert_pdf_equal(pdf, HERE / "palette_defaults.pdf", tmp_path)


def test_out_of_range_palette(tmp_path, caplog):
    """Test that out-of-range palette indices are handled gracefully with warning."""
    pdf = FPDF()

    # This should not raise an error, should fall back to palette 0 and log a warning
    pdf.add_font("Nabla-OOR", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=999)

    pdf.add_page()
    pdf.set_font("Nabla-OOR", size=24)
    pdf.cell(text="OUT OF RANGE")

    # Check that a warning was logged about the out-of-range palette
    assert any("out of range" in record.message.lower() or "palette" in record.message.lower() 
               for record in caplog.records if record.levelname == "WARNING")
    
    assert_pdf_equal(pdf, HERE / "out_of_range_palette.pdf", tmp_path)


def test_multiple_palettes_same_font(tmp_path):
    """Test using multiple palettes from the same font file."""
    pdf = FPDF()
    
    # Add the same font with different palettes using different family names
    pdf.add_font("Nabla-P0", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=0)
    pdf.add_font("Nabla-P1", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=1)
    pdf.add_font("Nabla-P2", "", HERE / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=2)
    
    pdf.add_page()
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(text="Palette 0:", new_x="lmargin", new_y="next")
    pdf.set_font("Nabla-P0", size=20)
    pdf.cell(text="HELLO", new_x="lmargin", new_y="next")
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(text="Palette 1:", new_x="lmargin", new_y="next")
    pdf.set_font("Nabla-P1", size=20)
    pdf.cell(text="HELLO", new_x="lmargin", new_y="next")
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(text="Palette 2:", new_x="lmargin", new_y="next")
    pdf.set_font("Nabla-P2", size=20)
    pdf.cell(text="HELLO", new_x="lmargin", new_y="next")
    
    assert_pdf_equal(pdf, HERE / "multiple_palettes_same_font.pdf", tmp_path)
