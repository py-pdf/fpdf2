from pathlib import Path

from fpdf import FPDF, HTMLMixin
from test.utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


class PDF(FPDF, HTMLMixin):
    pass


def test_links(tmp_path):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)
    line_height = 10

    pdf.set_xy(80, 50)
    pdf.cell(
        w=40,
        h=line_height,
        txt="Cell link",
        border=1,
        align="C",
        link="https://github.com/PyFPDF/fpdf2",
    )

    pdf.set_xy(60, 100)
    pdf.write_html('<a href="https://github.com/PyFPDF/fpdf2">Link defined as HTML</a>')

    text = "Text link"
    pdf.text(x=80, y=150, txt=text)
    width = pdf.get_string_width(text)
    pdf.link(x=0, y=0, w=width, h=line_height, link="https://github.com/PyFPDF/fpdf2")

    pdf.add_page()
    link = pdf.add_link()
    pdf.set_link(link, page=1)
    pdf.set_xy(50, 50)
    pdf.cell(
        w=100, h=10, txt="Internal link to first page", border=1, align="C", link=link
    )

    assert_pdf_equal(pdf, HERE / "links.pdf", tmp_path)
