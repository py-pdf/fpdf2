from pathlib import Path

from fpdf import FPDF
from fpdf import FPDF_VERSION

DIR = Path(__file__).parent
FONT_DIR = DIR / ".." / "test" / "fonts"

pdf = FPDF(enforce_compliance="PDF/A-3B")
pdf.set_lang("en-US")
pdf.set_title("Tutorial7")
pdf.set_author(["John Dow", "Jane Dow"])
pdf.set_subject("Example for PDF/A")
pdf.set_keywords(["example", "tutorial", "fpdf", "pdf/a"])
pdf.set_producer(f"py-pdf/fpdf2 {FPDF_VERSION}")
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

pdf.output("tuto7.pdf")
