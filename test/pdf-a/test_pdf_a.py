from pathlib import Path

from fpdf import FPDF
from fpdf.enums import DocumentCompliance

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / ".." / "fonts"


def test_basic_pdfa(tmp_path):
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_3B)
    pdf.set_lang("en-US")
    pdf.set_title("Tutorial7")
    pdf.set_subject("Example for PDFA")
    pdf.set_author(["John Dow", "Jane Dow"])
    pdf.set_keywords(["Example", "Tutorial7", "PDF/A"])
    pdf.add_font(fname=FONT_DIR / "DejaVuSans.ttf")
    pdf.add_font("DejaVuSans", style="B", fname=FONT_DIR / "DejaVuSans-Bold.ttf")
    pdf.add_font("DejaVuSans", style="I", fname=FONT_DIR / "DejaVuSans-Oblique.ttf")
    pdf.add_page()
    pdf.set_font("DejaVuSans", style="B", size=20)
    pdf.write(text="Header")
    pdf.ln(20)
    pdf.set_font(size=12)
    pdf.write(text="Example text")
    pdf.ln(20)
    pdf.set_font(style="I")
    pdf.write(text="Example text in italics")
    assert_pdf_equal(pdf, HERE / "basic_pdfa.pdf", tmp_path)


def test_pdfa_font_fallback(tmp_path):
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_2B)
    pdf.add_page()
    pdf.add_font(family="Quicksand", fname=FONT_DIR / "Quicksand-Regular.otf")
    pdf.add_font(family="Roboto", fname=FONT_DIR / "Roboto-Regular.ttf")
    pdf.add_font(family="DejaVuSans", fname=FONT_DIR / "DejaVuSans.ttf")
    pdf.add_font(family="TwitterEmoji", fname=FONT_DIR / "TwitterEmoji.ttf")
    pdf.add_font(family="Waree", fname=FONT_DIR / "Waree.ttf")
    text = "Hello world / สวัสดีชาวโลก ทดสอบฟอนต์, 😄 😁 😆 😅 ✌"
    pdf.set_fallback_fonts(
        ["DejaVuSans", "Quicksand", "Waree", "TwitterEmoji", "Roboto"]
    )
    pdf.set_text_shaping(True)
    pdf.set_font("TwitterEmoji", size=20)
    pdf.cell(text=text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln()
    pdf.set_font("Roboto", size=20)
    pdf.cell(text=text, new_x="LMARGIN", new_y="NEXT")
    assert_pdf_equal(pdf, HERE / "pdfa_fallback_fonts.pdf", tmp_path)


def test_pdfa_png_image(tmp_path):
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_3B)
    pdf.add_page()
    pdf.image(
        HERE / ".." / "image" / "png_images" / "ac6343a98f8edabfcc6e536dd75aacb0.png",
        x=0,
        y=0,
        w=0,
        h=0,
    )
    assert_pdf_equal(pdf, HERE / "pdfa_image_png.pdf", tmp_path)
