#!/usr/bin/env python3
"""
Visual validation script for rounded corners rendering fix.

This script generates a PDF that demonstrates the fix for two rendering issues:
1. Thick borders causing positioning issues with corner arcs
2. Fill colors showing visible line artifacts at corners

Run this script to manually verify the fix works correctly:
    python scripts/validate_round_corners_fix.py

The generated PDF should show:
- Top rectangle: Smooth, perfectly rounded corners with thick black border (no gaps/misalignment)
- Bottom rectangle: Clean pink fill with no visible line artifacts at corners

Related PR: Fix rounded rectangle rendering issues with thick borders and fill artifacts
"""

from fpdf import FPDF


def main():
    """Generate validation PDF for rounded corners fix."""
    pdf = FPDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Rounded Corners Fix - Visual Validation", ln=True, align="C")
    pdf.ln(5)
    
    # Test 1: Thick border (6pt) with white fill
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Test 1: Thick border (6pt) - Should have smooth corners", ln=True)
    pdf.ln(5)
    
    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_line_width(6)
    pdf.rect(50, 40, 120, 70, style='DF', round_corners=True, corner_radius=12)
    
    # Test 2: Thin border (1pt) with pink fill
    pdf.set_xy(10, 120)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Test 2: Pink fill (1pt border) - No line artifacts at corners", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 120, 125)
    pdf.set_line_width(1)
    pdf.rect(50, 160, 120, 70, style='DF', round_corners=True, corner_radius=12)
    
    # Output
    output_file = "validation_round_corners.pdf"
    pdf.output(output_file)
    
    print(f"✅ Generated: {output_file}")
    print("\n📄 Open the PDF to visually verify:")
    print("   ✓ Top rectangle: Smooth corners with thick border (no gaps/misalignment)")
    print("   ✓ Bottom rectangle: Clean pink fill (no visible line artifacts)")
    print("\n💡 Compare with the reproduction code from the issue to see the improvement.")


if __name__ == "__main__":
    main()
