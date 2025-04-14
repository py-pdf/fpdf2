from pathlib import Path

import markdown
import pytest

from fpdf import FPDF
from fpdf.errors import FPDFUnicodeEncodingException, FPDFException

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize("md_text", ["# Hello __world__"])
def test_save_text_as_img_markdown(
    md_text: str, font_size=16, font_family="dejavusans"
):

    # Parse Markdown to HTML
    html = markdown.markdown(md_text)

    # Create a PDF object
    pdf = FPDF()
    try:
        # Add the HTML to the PDF
        pdf.add_page()
        pdf.add_font(
            "dejavusans",
            fname= (HERE.parent / 'fonts/DejaVuSans.ttf').absolute().__str__(),
        )
        pdf.add_font(
            "dejavusansB",
            fname=(HERE.parent / 'fonts/DejaVuSans-Bold.ttf').absolute().__str__()
        )
        pdf.set_font("dejavusans", style="", size=font_size)
        pdf.set_text_color(0, 0, 0)
        pdf.write_html(html, font_family=font_family)
    except FPDFException:
        pytest.fail('')
