import os
from fpdf import FPDF
from fpdf.enums import OutputIntentSubType
from fpdf.output import PDFICCProfileObject
from fpdf import FPDF_VERSION
from datetime import datetime, timezone
import pikepdf


class PDF(FPDF):
    """class for my pdf inherited from FPDF
    """
    def __init__(self):
        super().__init__()
        """
        import and embed TTF Font to use in text
        """
        self.add_font(
            "dejavu-sans", style="",
            fname="./assets/Fonts/DejaVuSansCondensed.ttf"
        )
        self.add_font(
            "dejavu-sans",
            style="b",
            fname="./assets/Fonts/DejaVuSansCondensed-Bold.ttf",
        )
        self.add_font(
            "dejavu-sans",
            style="i",
            fname="./assets/Fonts/DejaVuSansCondensed-Oblique.ttf",
        )
        self.add_font(
            "dejavu-sans",
            style="bi",
            fname="./assets/Fonts/DejaVuSansCondensed-BoldOblique.ttf",
        )
        # set Output Intents
        with open(os.path.join("assets", "sRGB2014.icc"), "rb") as\
                iccp_file:
            icc_profile = PDFICCProfileObject(
                contents=iccp_file.read(),
                n=3,
                alternate="DeviceRGB"
            )
        self.add_output_intent(
            OutputIntentSubType.PDFA,
            "sRGB",
            "IEC 61966-2-1:1999",
            "http://www.color.org",
            icc_profile,
            "sRGB2014 (v2)",
        )

    def create_pdf_with_metadata(self,
                                 filename: str,
                                 language: str = None,
                                 title: str = None,
                                 subject: str = None,
                                 creator: list = None,
                                 description: str = None,
                                 keywords: str = None,
                                 ):
        # don't set metadata with this
        # pdf.set_title("Tutorial 7")
        # pdf.set_author("John Doe")
        # pdf.set_producer(f"py-pdf/fpdf{FPDF_VERSION}")
        # except:
        if language:
            self.set_lang(language)
        if subject:
            self.set_subject(subject)

        # create pdf
        self.output(filename)

        with pikepdf.open(filename, allow_overwriting_input=True) as pdf:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                if title:
                    meta["dc:title"] = title
                # meta["dc:language"] = "en-US"
                #   not compliant to PDFA-3B
                if creator:
                    meta["dc:creator"] = creator
                if description:
                    meta["dc:description"] = description
                # meta["dc:subject"] = "Example for PDFA"
                #   not compliant to PDFA-3B
                if keywords:
                    meta["pdf:Keywords"] = keywords
                meta["pdf:Producer"] = f"py-pdf/fpdf{FPDF_VERSION}"
                meta["xmp:CreatorTool"] = __file__
                meta["xmp:CreateDate"] = datetime.now(timezone.utc).isoformat()
                meta["pdfaid:part"] = "3"
                meta["pdfaid:conformance"] = "B"
            pdf.save()


pdf = PDF()
# First page:
pdf.add_page()
# use the font imported
# and set style and size for H1
pdf.set_font("dejavu-sans", "B", size=20)
pdf.write(text="Header 1")
# print empty lines
pdf.ln()
pdf.ln()
# reset style and set size for normal Text
pdf.set_font(None, "", size=12)
pdf.write(text="this is an example")
# print empty lines
pdf.ln()
pdf.ln()
# set style for Text 2 to italic
pdf.set_font(None, "I")
pdf.write(text="this is the second example")

# create pdf with metadata
pdf.create_pdf_with_metadata(
    filename="tuto7.pdf",
    language="en-US",
    title="Tutorial7",
    subject="Example for PDFA",
    creator=["John Dow", "Jane Dow"],
    description="this is my description of this file",
    keywords="Example Tutorial7"
)
