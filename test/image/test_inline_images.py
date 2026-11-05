"""
Unit tests for inline images (raster and vector) with write() and write_image().
Tests vertical alignments (TOP, MIDDLE, BOTTOM), keep_aspect_ratio, multiple images per line,
and automatic line-wrapping with multi-line flowing text.
"""

import io
from pathlib import Path
from PIL import Image, ImageDraw

from fpdf import FPDF, VAlign
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
SVG_PATH = HERE / "../svg/svg_sources/SVG_logo_fixed_dimensions.svg"
FONTS_DIR = HERE / "../fonts"


def _create_sample_image(path: Path) -> None:
    img = Image.new("RGB", (100, 30), color=(230, 240, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 99, 29], outline=(100, 120, 200))
    d.text((10, 8), "e^(i*pi) + 1 = 0", fill=(10, 40, 120))
    img.save(path)


def test_inline_image_all_scenarios(tmp_path):
    """
    Comprehensive test producing a 4-page PDF covering all inline image scenarios:
    1. VAlign: TOP, MIDDLE, BOTTOM with raster and SVG images across standard & styled fonts.
    2. Dynamic in-memory placeholders (PIL.Image, io.BytesIO, raw bytes) and template token substitution.
    3. Flowing paragraph wrapping across lines with inline image, multi-image equations, and font styles.
    4. Sizing combinations, aspect ratio preservation, stretch, and font types (CoreFont Times/Courier, TrueType TTF).
    """
    img_path = tmp_path / "sample_eq.png"
    _create_sample_image(img_path)

    pdf = FPDF()

    # --- Page 1: VAlign Scenarios & Font Style Continuity (TOP, MIDDLE, BOTTOM) ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", size=14)
    pdf.write(text="Inline Image Vertical Alignments & Font Styles\n\n")

    # 1. VAlign.T (Top) with Bold font style
    pdf.set_font("Helvetica", "B", size=11)
    pdf.write(text="1. VAlign.T (Bold text): Text before ")
    pdf.write_image(img_path, h=7, valign=VAlign.T)
    pdf.write(text=" and text after image preserves bold style.\n\n")

    # 2. VAlign.M (Middle) with Italic font style
    pdf.set_font("Helvetica", "I", size=11)
    pdf.write(text="2. VAlign.M (Italic text): Text before ")
    pdf.write_image(img_path, h=7, valign=VAlign.M)
    pdf.write(text=" and text after image preserves italic style.\n\n")

    # 3. VAlign.B (Bottom) with Underline font style
    pdf.set_font("Helvetica", "U", size=11)
    pdf.write(text="3. VAlign.B (Underlined text): Text before ")
    pdf.write_image(img_path, h=7, valign=VAlign.B)
    pdf.write(text=" and text after image preserves underline style.\n\n")

    # 4. Vector SVG inline with combined Bold-Italic-Underline font style
    if SVG_PATH.exists():
        pdf.set_font("Helvetica", "BIU", size=11)
        pdf.write(text="4. Vector SVG (BIU text): SVG icon ")
        pdf.write_image(str(SVG_PATH), h=7, valign=VAlign.M)
        pdf.write(text=" rendered inline preserving BIU style.\n\n")

    # --- Page 2: In-Memory Dynamic Placeholders & Template Replacement ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", size=14)
    pdf.write(text="Dynamic In-Memory Placeholders & Token Substitution\n\n")

    pdf.set_font("Helvetica", size=10)

    # 1. In-memory dynamic PIL Image placeholder badge
    badge_pil = Image.new("RGBA", (140, 32), color=(46, 125, 50, 255))
    d_badge = ImageDraw.Draw(badge_pil)
    d_badge.text((12, 8), "PASSED [100%]", fill=(255, 255, 255, 255))

    pdf.write(text="Build Status: ")
    pdf.write_image(badge_pil, h=5.5, valign=VAlign.M)
    pdf.write(text=" verified by automated test harness.\n\n")

    # 2. BytesIO / raw bytes in-memory placeholder
    buf = io.BytesIO()
    badge_pil.save(buf, format="PNG")
    buf.seek(0)
    pdf.write(text="From BytesIO Stream: ")
    pdf.write_image(buf, h=5.5, valign=VAlign.M)
    pdf.write(text=" with instant in-memory rendering.\n\n")

    # 3. Placeholder Token Replacement Workflow
    template = "Invoice item: [ITEM_LOGO] Product Model X ($499.00)"
    parts = template.split("[ITEM_LOGO]")
    pdf.write(text=parts[0])
    pdf.write_image(img_path, h=6, valign=VAlign.M)
    pdf.write(text=f"{parts[1]}\n\n")

    # --- Page 3: Multi-image Sequence & Multi-line Wrapping ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", size=14)
    pdf.write(text="Inline Images Flow & Multi-line Wrapping\n\n")

    pdf.set_font("Helvetica", size=10)

    # 1. Multiple inline images in a formula/row
    pdf.write(text="Inline Equation Sequence: ")
    pdf.write_image(img_path, h=6, valign=VAlign.M)
    pdf.write(text=" + ")
    pdf.write_image(img_path, h=6, valign=VAlign.M)
    pdf.write(text=" = [Result]\n\n")

    # 2. Flowing paragraph wrapping across lines with inline image
    pdf.write(
        text="This paragraph tests multi-line word wrapping around inline images. "
        "We append continuous text to approach the right page margin so the inline image "
    )
    pdf.write_image(img_path, h=7, valign=VAlign.M)
    pdf.write(
        text=" is immediately followed by more text that automatically wraps to the next line. "
        "Notice that the subsequent text line is placed cleanly below the expanded line height "
        "without clipping or overlapping into the image."
    )

    # --- Page 4: Sizing, Aspect Ratio & Font Types (CoreFont / TTF) ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", size=14)
    pdf.write(text="Sizing, Aspect Ratio & Font Types\n\n")

    # 1. Default auto-sizing (w=0, h=0) in Times CoreFont
    pdf.set_font("Times", size=10)
    pdf.write(text="1. Times CoreFont & Auto-size (w=0, h=0): ")
    pdf.write_image(img_path, w=0, h=0)
    pdf.write(text=" (matches current font size height).\n\n")

    # 2. Width only (w=25, h=0) in Courier CoreFont
    pdf.set_font("Courier", size=10)
    pdf.write(text="2. Courier CoreFont & Width only (w=25, h=0): ")
    pdf.write_image(img_path, w=25, h=0)
    pdf.write(text=" (height from aspect ratio).\n\n")

    # 3. Height only (w=0, h=7.5) with TrueType TTF Font (DejaVuSans)
    pdf.add_font("DejaVu", fname=FONTS_DIR / "DejaVuSans.ttf")
    pdf.set_font("DejaVu", size=10)
    pdf.write(text="3. DejaVu TTF (Unicode: ∑ ∫ π) & Height (h=7.5): ")
    pdf.write_image(img_path, w=0, h=7.5)
    pdf.write(text=" (proportional width in TTF).\n\n")

    # 4. Box fit with keep_aspect_ratio=True (w=30, h=14)
    pdf.set_font("Helvetica", size=10)
    pdf.write(text="4. Fit inside box (w=30, h=14, keep_aspect_ratio=True): ")
    pdf.write_image(img_path, w=30, h=14, keep_aspect_ratio=True)
    pdf.write(text=" (ratio preserved).\n\n")

    # 5. Box stretch with keep_aspect_ratio=False (w=15, h=10)
    pdf.write(text="5. Explicit stretch (w=15, h=10, keep_aspect_ratio=False): ")
    pdf.write_image(img_path, w=15, h=10, keep_aspect_ratio=False)
    pdf.write(text=" (exact bounding dimensions).\n\n")

    assert_pdf_equal(pdf, HERE / "inline_images_all_scenarios.pdf", tmp_path)
