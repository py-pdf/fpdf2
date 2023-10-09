from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent


def test_hyperlinks(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)

    pdf.y = 50
    pdf.cell(
        txt="Link from FPDF.cell()",
        center=True,
        link="https://github.com/py-pdf/fpdf2",
    )

    pdf.set_xy(60, 100)
    pdf.write_html('<a href="https://py-pdf.github.io/fpdf2/">Link defined as HTML</a>')

    text = "Link set over an arbitrary area with FPDF.link()"
    x, y = 20, 150
    pdf.text(x=x, y=y, txt=text)
    width = pdf.get_string_width(text)
    pdf.link(
        x=x,
        y=y - pdf.font_size,
        w=width,
        h=pdf.font_size,
        link="https://github.com/py-pdf/fpdf2/discussions",
    )

    assert_pdf_equal(pdf, HERE / "hyperlinks.pdf", tmp_path)


def test_link_alt_text(tmp_path):
    """
    It can be tested that the reference file for this test
    has the link description read out loud by the NVDA screen reader
    when opened with Adobe Acrobat Reader.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)
    text = "py-pdf/fpdf2"
    pdf.text(x=80, y=150, txt=text)
    width = pdf.get_string_width(text)
    line_height = 10
    pdf.link(
        x=80,
        y=150 - line_height,
        w=width,
        h=line_height,
        link="https://github.com/py-pdf/fpdf2",
        alt_text="GitHub repository of the fpdf2 library",
    )
    assert_pdf_equal(pdf, HERE / "link_alt_text.pdf", tmp_path)


def test_link_with_zoom_and_shift(tmp_path):
    pdf = FPDF()
    pdf.set_font("helvetica", size=24)
    pdf.add_page()
    link = pdf.add_link()
    pdf.set_link(link, page=2, x=pdf.epw / 4, y=pdf.epw / 3, zoom=4)
    pdf.set_xy(30, 50)
    pdf.cell(
        w=140,
        h=10,
        txt="Link to 2nd page zoomed & shifted",
        border=1,
        align="C",
        link=link,
    )
    pdf.add_page()
    pdf.multi_cell(
        pdf.epw,
        txt="Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
        " sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        " Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
        " Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
        " Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    )
    # Drawing Adobe Reader viewport after clicking on the link,
    # with the right panel open. The initial zoom level does not matter.
    pdf.set_draw_color(r=255, g=0, b=0)
    pdf.rect(x=pdf.epw / 4, y=pdf.epw / 3, w=53.5, h=31)
    assert_pdf_equal(pdf, HERE / "link_with_zoom_and_shift.pdf", tmp_path)


def test_link_border(tmp_path):
    "Acrobat renders this border it but not Sumatra"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)

    text = "https://github.com/py-pdf/fpdf2"
    height = 10
    x, y = 50, 150

    pdf.text(x=x, y=y, txt=text)
    pdf.link(
        x=x,
        y=y - height,
        w=pdf.get_string_width(text),
        h=height,
        link="https://github.com/py-pdf/fpdf2",
        border_width=4,
    )

    assert_pdf_equal(pdf, HERE / "link_border.pdf", tmp_path)


def test_inserting_same_page_link_twice(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.link(
        x=pdf.l_margin,
        y=pdf.t_margin,
        w=pdf.epw,
        h=pdf.eph,
        link=pdf.add_link(page=2),
    )
    pdf.add_page()
    pdf.link(
        x=pdf.l_margin,
        y=pdf.t_margin,
        w=pdf.epw,
        h=pdf.eph,
        link=pdf.add_link(page=2),
    )
    assert_pdf_equal(pdf, HERE / "inserting_same_page_link_twice.pdf", tmp_path)


def test_inserting_link_to_non_exising_page():
    pdf = FPDF()
    pdf.add_page()
    pdf.link(
        x=pdf.l_margin,
        y=pdf.t_margin,
        w=pdf.epw,
        h=pdf.eph,
        link=pdf.add_link(page=2),
    )
    with pytest.raises(ValueError):
        pdf.output()


def test_inserting_link_with_no_page_number():
    pdf = FPDF()
    link = pdf.add_link()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    with pytest.raises(ValueError):
        pdf.cell(txt="Page 1", link=link)


def test_later_call_to_set_link(tmp_path):  # v2.6.1 bug spotted in discussion 729
    pdf = FPDF()
    pdf.set_font("helvetica")

    pdf.add_page()  # page 1
    link_to_section1 = pdf.add_link()
    pdf.cell(txt="Section 1", link=link_to_section1)

    pdf.add_page()  # page 2
    pdf.set_link(link_to_section1, page=pdf.page)
    pdf.cell(txt="Section 1: Bla bla bla")

    assert_pdf_equal(pdf, HERE / "later_call_to_set_link.pdf", tmp_path)


def test_link_to_other_document(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)

    pdf.set_xy(80, 50)
    pdf.cell(
        txt="Link defined with FPDF.cell",
        border=1,
        align="C",
        link="links.pdf",
    )

    pdf.set_y(100)
    pdf.multi_cell(
        w=pdf.epw,
        txt="Link defined with FPDF.multi_cell",
        border=1,
        align="C",
        link="links.pdf",
    )

    pdf.set_y(150)
    pdf.multi_cell(
        w=pdf.epw,
        txt="Link defined with FPDF.multi_cell and markdown=True: [links.pdf](links.pdf)",
        border=1,
        align="C",
        markdown=True,
    )

    pdf.set_xy(60, 200)
    pdf.write_html('<a href="links.pdf">Link defined with FPDF.write_html</a>')

    text = "Link defined with FPDF.link"
    pdf.text(x=80, y=250, txt=text)
    width = pdf.get_string_width(text)
    pdf.link(
        x=80,
        y=250 - pdf.h,
        w=width,
        h=pdf.h,
        link="links.pdf",
    )

    assert_pdf_equal(pdf, HERE / "link_to_other_document.pdf", tmp_path)


def test_internal_links(tmp_path):
    pdf = FPDF()
    pdf.set_font("helvetica", size=24)

    pdf.add_page()
    pdf.y = 100
    pdf.cell(txt="Page 1", center=True)

    pdf.add_page()

    pdf.set_xy(80, 50)
    pdf.cell(
        txt="Link defined with FPDF.cell",
        border=1,
        align="C",
        link=pdf.add_link(page=1),
    )

    pdf.set_y(100)
    pdf.multi_cell(
        w=pdf.epw,
        txt="Link defined with FPDF.multi_cell",
        border=1,
        align="C",
        link=pdf.add_link(page=1),
    )

    pdf.set_y(150)
    pdf.multi_cell(
        w=pdf.epw,
        txt="Link defined with FPDF.multi_cell and markdown=True: [page 1](1)",
        border=1,
        align="C",
        markdown=True,
    )

    pdf.set_xy(60, 200)
    pdf.write_html('<a href="1">Link defined with FPDF.write_html</a>')

    text = "Link defined with FPDF.link"
    pdf.text(x=80, y=250, txt=text)
    width = pdf.get_string_width(text)
    pdf.link(
        x=80,
        y=250 - pdf.h,
        w=width,
        h=pdf.h,
        link=pdf.add_link(page=1),
    )

    assert_pdf_equal(pdf, HERE / "internal_links.pdf", tmp_path)
