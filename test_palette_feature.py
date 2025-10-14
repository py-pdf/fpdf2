"""
Test script to demonstrate the palette selection feature for color fonts.
This script creates PDFs using different palettes from a color font.
"""

from pathlib import Path
from fpdf import FPDF

# Path to test fonts
TEST_DIR = Path(__file__).resolve().parent / "test" / "color_font"

def test_palette_selection():
    """
    Test the palette parameter in add_font() method.
    This demonstrates using different palettes from a color font.
    """
    
    # Example 1: Using default palette (palette 0)
    print("Creating PDF with default palette (palette 0)...")
    pdf = FPDF()
    pdf.add_font("Nabla", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=0)
    pdf.add_page()
    pdf.set_font("Nabla", size=24)
    pdf.cell(text="HELLO WORLD - Palette 0", new_x="lmargin", new_y="next")
    pdf.output("test_palette_0.pdf")
    print("✓ Created test_palette_0.pdf")
    
    # Example 2: Using palette 1 (if available)
    print("\nCreating PDF with palette 1...")
    pdf2 = FPDF()
    pdf2.add_font("Nabla-Blue", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=1)
    pdf2.add_page()
    pdf2.set_font("Nabla-Blue", size=24)
    pdf2.cell(text="HELLO WORLD - Palette 1", new_x="lmargin", new_y="next")
    pdf2.output("test_palette_1.pdf")
    print("✓ Created test_palette_1.pdf")
    
    # Example 3: Using palette 2 (if available)
    print("\nCreating PDF with palette 2...")
    pdf3 = FPDF()
    pdf3.add_font("Nabla-Grey", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=2)
    pdf3.add_page()
    pdf3.set_font("Nabla-Grey", size=24)
    pdf3.cell(text="HELLO WORLD - Palette 2", new_x="lmargin", new_y="next")
    pdf3.output("test_palette_2.pdf")
    print("✓ Created test_palette_2.pdf")
    
    # Example 4: Comparison PDF with all three palettes
    print("\nCreating comparison PDF with all palettes...")
    pdf_compare = FPDF()
    pdf_compare.add_font("Nabla", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=0)
    pdf_compare.add_font("Nabla-Blue", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=1)
    pdf_compare.add_font("Nabla-Grey", "", TEST_DIR / "Nabla-Regular-COLRv1-VariableFont_EDPT,EHLT.ttf", palette=2)
    
    pdf_compare.add_page()
    pdf_compare.set_font("helvetica", "", 16)
    pdf_compare.cell(text="Color Font Palette Comparison", new_x="lmargin", new_y="next")
    pdf_compare.ln(5)
    
    pdf_compare.set_font("helvetica", "", 12)
    pdf_compare.cell(text="Palette 0 (Default):", new_x="lmargin", new_y="next")
    pdf_compare.set_font("Nabla", size=20)
    pdf_compare.cell(text="HELLO WORLD", new_x="lmargin", new_y="next")
    pdf_compare.ln(5)
    
    pdf_compare.set_font("helvetica", "", 12)
    pdf_compare.cell(text="Palette 1:", new_x="lmargin", new_y="next")
    pdf_compare.set_font("Nabla-Blue", size=20)
    pdf_compare.cell(text="HELLO WORLD", new_x="lmargin", new_y="next")
    pdf_compare.ln(5)
    
    pdf_compare.set_font("helvetica", "", 12)
    pdf_compare.cell(text="Palette 2:", new_x="lmargin", new_y="next")
    pdf_compare.set_font("Nabla-Grey", size=20)
    pdf_compare.cell(text="HELLO WORLD", new_x="lmargin", new_y="next")
    
    pdf_compare.output("test_palette_comparison.pdf")
    print("✓ Created test_palette_comparison.pdf")
    
    print("\n" + "="*60)
    print("SUCCESS! All test PDFs created successfully.")
    print("="*60)
    print("\nGenerated files:")
    print("  - test_palette_0.pdf")
    print("  - test_palette_1.pdf")
    print("  - test_palette_2.pdf")
    print("  - test_palette_comparison.pdf")

if __name__ == "__main__":
    test_palette_selection()
