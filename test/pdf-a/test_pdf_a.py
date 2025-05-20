import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import OutputIntentSubType
from fpdf.output import PDFICCProfile
from fpdf import FPDF_VERSION
import pikepdf

import pytest

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / ".." / "fonts"
TUTORIAL = HERE / ".." / ".." / "tutorial"


class PDF(FPDF):
    def __init__(
        self, *args, language, title, subject, creator, description, keywords, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.language = language
        self.title = title
        self.subject = subject
        self.creator = creator
        self.description = description
        self.keywords = keywords

    def output(self, name: str, *args, **kwargs):
        if self.language:
            self.set_lang(self.language)
        if self.subject:
            self.set_subject(self.subject)
        super().output(name, *args, **kwargs)
        if hasattr(name, "name"):  # => io.BufferedWriter from assert_pdf_equal()
            name.close()  # closing buffer before opening file with pikepdf (required on Windows)
            name = name.name
        with pikepdf.open(name, allow_overwriting_input=True) as pdf:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                if self.title:
                    meta["dc:title"] = self.title
                if self.creator:
                    meta["dc:creator"] = self.creator
                if self.description:
                    meta["dc:description"] = self.description
                if self.keywords:
                    meta["pdf:Keywords"] = self.keywords
                meta["pdf:Producer"] = f"py-pdf/fpdf2"
                meta["xmp:CreatorTool"] = __name__
                # meta["xmp:CreateDate"] = already done by assert_pdf_equal()
                meta["pdfaid:part"] = "3"
                meta["pdfaid:conformance"] = "B"
            pdf.save(deterministic_id=True)


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Fails on Python 3.8 because the PDFFontStream contents change",
)
def test_basic_pdfa(tmp_path):
    pdf = PDF(
        language="en-US",
        title="Tutorial7",
        subject="Example for PDFA",
        creator=["John Dow", "Jane Dow"],
        description="this is my description of this file",
        keywords="Example Tutorial7",
    )
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
    with open(TUTORIAL / "sRGB2014.icc", "rb") as iccp_file:
        icc_profile = PDFICCProfile(
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
    assert_pdf_equal(pdf, HERE / "basic_pdfa.pdf", tmp_path)
