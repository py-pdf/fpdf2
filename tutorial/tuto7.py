from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import OutputIntentSubType
from fpdf.output import PDFICCProfileObject
from fpdf import FPDF_VERSION
import pikepdf


DIR = Path(__file__).parent
FONT_DIR = DIR / ".." / "test" / "fonts"


def create_pdf_with_metadata(
    fpdf: FPDF,
    filename: str,
    language: str = None,
    title: str = None,
    subject: str = None,
    creator: list = None,
    description: str = None,
    keywords: str = None,
):
    if language:
        fpdf.set_lang(language)
    if subject:
        fpdf.set_subject(subject)
    fpdf.output(filename)  # Produces a first version of the .pdf
    # Now add metadata with pikepdf
    with pikepdf.open(filename, allow_overwriting_input=True) as pike_pdf:
        with pike_pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            if title:
                meta["dc:title"] = title
            if creator:
                meta["dc:creator"] = creator
            if description:
                meta["dc:description"] = description
            if keywords:
                meta["pdf:Keywords"] = keywords
            meta["pdf:Producer"] = f"py-pdf/fpdf{FPDF_VERSION}"
            meta["xmp:CreatorTool"] = __file__
            meta["xmp:CreateDate"] = datetime.now(timezone.utc).isoformat()
            meta["pdfaid:part"] = "3"
            meta["pdfaid:conformance"] = "B"
        pike_pdf.save()


pdf = FPDF()
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

# set Output Intents
with open(DIR / "sRGB2014.icc", "rb") as iccp_file:
    icc_profile = PDFICCProfileObject(
        contents=iccp_file.read(), n=3, alternate="DeviceRGB"
    )
pdf.add_output_intent(
    OutputIntentSubType.PDFA,
    "sRGB",
    "IEC 61966-2-1:1999",
    "http://www.color.org",
    icc_profile,
    "sRGB2014 (v2)",
)

create_pdf_with_metadata(
    pdf,
    filename="tuto7.pdf",
    language="en-US",
    title="Tutorial7",
    subject="Example for PDFA",
    creator=["John Dow", "Jane Dow"],
    description="this is my description of this file",
    keywords="Example Tutorial7",
)
