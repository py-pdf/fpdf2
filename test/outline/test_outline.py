from pathlib import Path

import pytest

from fpdf import FPDF, TitleStyle, errors
from fpdf.outline import build_outline, outline_as_str
from fpdf.syntax import iobj_ref as pdf_ref

from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_simple_outline(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.set_section_title_styles(
        # Level 0 titles:
        TitleStyle(
            font_family="Times",
            font_style="B",
            font_size_pt=24,
            color=128,
            underline=True,
            t_margin=10,
            l_margin=10,
            b_margin=0,
        ),
        # Level 1 subtitles:
        TitleStyle(
            font_family="Times",
            font_style="B",
            font_size_pt=20,
            color=128,
            underline=True,
            t_margin=10,
            l_margin=20,
            b_margin=5,
        ),
    )

    pdf.add_page()
    pdf.set_y(50)
    pdf.set_font(size=40)
    p(pdf, "Doc Title", align="C")
    pdf.set_font(size=12)
    pdf.insert_toc_placeholder(render_toc)
    pdf.start_section("Title 1")
    pdf.start_section("Subtitle 1.1", level=1)
    p(
        pdf,
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
        " sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    )
    pdf.add_page()
    pdf.start_section("Subtitle 1.2", level=1)
    p(
        pdf,
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    )
    pdf.add_page()
    pdf.start_section("Title 2")
    pdf.start_section("Subtitle 2.1", level=1)
    p(
        pdf,
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    )
    pdf.add_page()
    pdf.start_section("Subtitle 2.2", level=1)
    p(
        pdf,
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    )
    assert_pdf_equal(pdf, HERE / "simple_outline.pdf", tmp_path)


def p(pdf, text, **kwargs):
    pdf.multi_cell(
        w=pdf.epw,
        h=pdf.font_size,
        txt=text,
        new_x="LMARGIN",
        new_y="NEXT",
        **kwargs,
    )


# pylint: disable=unused-argument
def render_toc(pdf, outline):
    pdf.y += 50
    pdf.set_font("Helvetica", size=16)
    pdf.underline = True
    p(pdf, "Table of contents:")
    pdf.underline = False
    pdf.y += 20
    pdf.set_font("Courier", size=12)
    for section in outline:
        link = pdf.add_link()
        pdf.set_link(link, page=section.page_number)
        text = f'{" " * section.level * 2} {section.name}'
        text += (
            f' {"." * (60 - section.level*2 - len(section.name))} {section.page_number}'
        )
        pdf.multi_cell(
            w=pdf.epw,
            h=pdf.font_size,
            txt=text,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
            link=link,
        )


def test_insert_toc_placeholder_with_invalid_arg_type():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(TypeError):
        pdf.insert_toc_placeholder("render_toc")


def test_insert_toc_placeholder_twice():
    pdf = FPDF()
    pdf.add_page()
    pdf.insert_toc_placeholder(render_toc)
    with pytest.raises(errors.FPDFException):
        pdf.insert_toc_placeholder(render_toc)


def test_incoherent_start_section_hierarchy():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        pdf.start_section("Title", level=-1)
    pdf.start_section("Title", level=0)
    with pytest.raises(ValueError):
        pdf.start_section("Subtitle", level=2)


def test_set_section_title_styles_with_invalid_arg_type():
    pdf = FPDF()
    with pytest.raises(TypeError):
        pdf.set_section_title_styles("Times")


def test_2_pages_outline(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.set_section_title_styles(
        # Level 0 titles:
        TitleStyle(
            font_family="Times",
            font_style="B",
            font_size_pt=24,
            color=128,
            underline=True,
            t_margin=10,
            l_margin=10,
            b_margin=0,
        ),
    )

    pdf.add_page()
    pdf.set_y(50)
    pdf.set_font(size=40)
    p(pdf, "Doc Title", align="C")
    pdf.set_font(size=12)
    pdf.insert_toc_placeholder(render_toc, pages=2)
    for i in range(40):
        pdf.start_section(f"Title {i}")
        p(
            pdf,
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
            " sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        )
    assert_pdf_equal(pdf, HERE / "2_pages_outline.pdf", tmp_path)


def test_russian_heading(tmp_path):  # issue-320
    pdf = FPDF()
    pdf.add_font("Roboto", style="B", fname="test/fonts/Roboto-Regular.ttf")
    pdf.set_font("Roboto", style="B")
    pdf.add_page()
    pdf.start_section("Русский, English, 1 2 3...")
    pdf.write(8, "Русский текст в параграфе.")
    assert_pdf_equal(pdf, HERE / "russian_heading.pdf", tmp_path)


def test_self_refering_outline(tmp_path):
    """
    Based on Jens Müller talk at NDSS: Processing Dangerous Paths.
    As of 2022, neither Adobe Acrobat nor Sumatra PDF readers seem vulnerable.
    """

    class CustomFPDF(FPDF):
        def _put_document_outline(self):
            self._outlines_obj_id = self.n + 1
            outline, outline_items = build_outline(
                self._outline, first_object_id=self._outlines_obj_id, fpdf=self
            )
            outline.first = f"<< /A << /First {pdf_ref(self._outlines_obj_id)} >> >>"
            outline_as_str(outline, outline_items, fpdf=self)

    pdf = CustomFPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    p(pdf, "Doc Title", align="C")
    pdf.start_section("Title 1")
    p(pdf, "Lorem ipsum dolor sit amet,")
    pdf.add_page()
    pdf.start_section("Title 2")
    p(pdf, "consectetur adipiscing elit,")
    assert_pdf_equal(pdf, HERE / "self_refering_outline.pdf", tmp_path)
