#!/usr/bin/env python
"""
Unicode Font Detection and Management Tutorial

This tutorial demonstrates how to use fpdf2's new Unicode font detection
and management features to automatically handle different scripts like
Cyrillic, Arabic, Chinese, etc.
"""

from fpdf import FPDF
from fpdf.unicode_font_utils import (
    UnicodeFontManager,
    get_unicode_font_recommendation,
    suggest_unicode_font_for_error,
)
from fpdf.unicode_script import UnicodeScript

def demonstrate_unicode_font_detection():
    """Demonstrate automatic Unicode font detection and recommendations."""
    
    print("=== Unicode Font Detection Demo ===\n")
    
    # Initialize the font manager
    manager = UnicodeFontManager()
    
    # List available fonts
    print("Available Unicode fonts on this system:")
    available_fonts = manager.list_available_unicode_fonts()
    for font_name, font_path in list(available_fonts.items())[:5]:  # Show first 5
        print(f"  - {font_name}: {font_path}")
    if len(available_fonts) > 5:
        print(f"  ... and {len(available_fonts) - 5} more fonts")
    print()
    
    # Test different scripts
    test_texts = [
        ("English", "Hello World"),
        ("Russian (Cyrillic)", "Привет, мир!"),
        ("Arabic", "مرحبا بالعالم"),
        ("Chinese (Han)", "你好世界"),
        ("Korean (Hangul)", "안녕하세요"),
        ("Japanese (Hiragana)", "こんにちは世界"),
        ("Hindi (Devanagari)", "नमस्ते दुनिया"),
        ("Thai", "สวัสดีชาวโลก"),
        ("Hebrew", "שלום עולם"),
    ]
    
    for script_name, text in test_texts:
        print(f"=== {script_name} ===")
        print(f"Text: {text}")
        
        # Detect script
        detected_script = manager.detect_script_in_text(text)
        if detected_script:
            print(f"Detected script: {detected_script.name}")
            
            # Get font recommendations
            recommendations = manager.get_recommended_fonts_for_script(detected_script)
            if recommendations:
                print("Recommended fonts:")
                for i, (font_name, font_path) in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {font_name}")
            else:
                print("No specific font recommendations available")
        else:
            print("No specific script detected (likely Latin/Common)")
        
        print()

def demonstrate_error_handling():
    """Demonstrate improved error handling with font suggestions."""
    
    print("=== Error Handling Demo ===\n")
    
    # Simulate the error that would occur with Cyrillic text
    error_text = "ul. Zapadna obikolna, sgradа 8"
    font_name = "helvetica"
    
    print(f"Text causing error: {error_text}")
    print(f"Font that failed: {font_name}")
    print()
    
    # Get helpful error suggestion
    suggestion = suggest_unicode_font_for_error(error_text, font_name)
    print("Helpful error message:")
    print(suggestion)
    print()

def create_multilingual_pdf():
    """Create a PDF with multiple scripts using automatic font detection."""
    
    print("=== Creating Multilingual PDF ===\n")
    
    pdf = FPDF()
    pdf.add_page()
    
    # Initialize font manager
    manager = UnicodeFontManager()
    
    # Test texts in different scripts
    test_texts = [
        ("English", "Hello World - This is English text"),
        ("Russian (Cyrillic)", "Привет, мир! - Это русский текст"),
        ("Arabic", "مرحبا بالعالم - هذا نص عربي"),
        ("Chinese (Han)", "你好世界 - 这是中文文本"),
        ("Korean (Hangul)", "안녕하세요 - 이것은 한국어 텍스트입니다"),
        ("Japanese (Hiragana)", "こんにちは世界 - これは日本語のテキストです"),
        ("Hindi (Devanagari)", "नमस्ते दुनिया - यह हिंदी पाठ है"),
        ("Thai", "สวัสดีชาวโลก - นี่คือข้อความภาษาไทย"),
        ("Hebrew", "שלום עולם - זה טקסט בעברית"),
    ]
    
    y_position = 20
    
    for script_name, text in test_texts:
        # Get font recommendation for this text
        recommendation = manager.get_font_recommendation_for_text(text)
        
        if recommendation:
            font_name, font_path = recommendation
            try:
                # Add the recommended font
                pdf.add_font(font_name, '', font_path)
                pdf.set_font(font_name, size=12)
                
                # Add text
                pdf.set_y(y_position)
                pdf.cell(0, 8, f"{script_name}: {text}", new_x="LMARGIN", new_y="NEXT")
                
                print(f"✓ {script_name}: Using {font_name}")
                y_position += 10
                
            except Exception as e:
                # Fallback to default font
                pdf.set_font("helvetica", size=12)
                pdf.set_y(y_position)
                pdf.cell(0, 8, f"{script_name}: [Font not available] {text}", new_x="LMARGIN", new_y="NEXT")
                print(f"✗ {script_name}: Font not available ({e})")
                y_position += 10
        else:
            # Use default font for Latin text
            pdf.set_font("helvetica", size=12)
            pdf.set_y(y_position)
            pdf.cell(0, 8, f"{script_name}: {text}", new_x="LMARGIN", new_y="NEXT")
            print(f"• {script_name}: Using default font")
            y_position += 10
    
    # Save the PDF
    filename = "multilingual_unicode_demo.pdf"
    pdf.output(filename)
    print(f"\nPDF saved as: {filename}")

def demonstrate_convenience_function():
    """Demonstrate the convenience function for quick font recommendations."""
    
    print("=== Convenience Function Demo ===\n")
    
    # Test the convenience function
    test_texts = [
        "Привет, мир!",
        "مرحبا بالعالم",
        "你好世界",
        "Hello World",
    ]
    
    for text in test_texts:
        recommendation = get_unicode_font_recommendation(text)
        if recommendation:
            font_name, font_path = recommendation
            print(f"Text: {text}")
            print(f"Recommended font: {font_name}")
            print(f"Font path: {font_path}")
        else:
            print(f"Text: {text}")
            print("No specific recommendation (likely Latin text)")
        print()

if __name__ == "__main__":
    print("fpdf2 Unicode Font Detection Tutorial")
    print("=" * 50)
    print()
    
    try:
        # Run demonstrations
        demonstrate_unicode_font_detection()
        demonstrate_error_handling()
        demonstrate_convenience_function()
        create_multilingual_pdf()
        
        print("Tutorial completed successfully!")
        
    except Exception as e:
        print(f"Error during tutorial: {e}")
        print("This might be due to missing fonts on your system.")
        print("The functionality will work when appropriate fonts are available.")
