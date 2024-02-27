from pathlib import Path

import pytest

from fpdf import FPDF, TitleStyle, errors

from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_simple_outline(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.set_y(50)
    pdf.set_font(size=40)
    p(pdf, "Doc Title", align="C")
    pdf.set_font(size=12)
    pdf.insert_toc_placeholder(render_toc)
    insert_test_content(pdf)
    assert_pdf_equal(pdf, HERE / "simple_outline.pdf", tmp_path)


def render_toc(pdf, outline):
    pdf.y += 50
    pdf.set_font("Helvetica", size=16)
    pdf.underline = True
    p(pdf, "Table of contents:")
    pdf.underline = False
    pdf.y += 20
    pdf.set_font("Courier", size=12)
    for section in outline:
        link = pdf.add_link(page=section.page_number)
        p(
            pdf,
            f'{" " * section.level * 2} {section.name} {"." * (60 - section.level*2 - len(section.name))} {section.page_number}',
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
            (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
                " sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            ),
        )
    assert_pdf_equal(pdf, HERE / "2_pages_outline.pdf", tmp_path)


def test_toc_with_nb_and_footer(tmp_path):  # issue-548
    class TestPDF(FPDF):
        def render_toc(self, outline):
            self.x = self.l_margin
            self.set_font(style="", size=12)
            for section in outline:
                self.ln()
                self.cell(text=section.name)

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    pdf = TestPDF()
    pdf.set_font(family="helvetica", size=12)
    pdf.add_page()
    pdf.insert_toc_placeholder(TestPDF.render_toc, pages=2)
    for i in range(1, 80):
        pdf.set_font(style="B")
        pdf.start_section(f"Section {i}")
        pdf.cell(text=f"Section {i}")
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "toc_with_nb_and_footer.pdf", tmp_path)


def test_toc_with_russian_heading(tmp_path):  # issue-320
    pdf = FPDF()
    pdf.add_font(fname="test/fonts/Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular")
    pdf.add_page()
    pdf.start_section("Русский, English, 1 2 3...")
    pdf.write(8, "Русский текст в параграфе.")
    assert_pdf_equal(pdf, HERE / "toc_with_russian_heading.pdf", tmp_path)


def test_toc_with_thai_headings(tmp_path):  # issue-458
    pdf = FPDF()
    for txt in [
        "ลักษณะเฉพาะของคุณ",
        "ระดับฮอร์โมนเพศชาย",
        "ระดับฮอร์โมนเพศหญิง",
        "hello",
    ]:
        pdf.add_page()
        pdf.start_section(txt)
    assert_pdf_equal(pdf, HERE / "toc_with_thai_headings.pdf", tmp_path)


def test_toc_without_font_style(tmp_path):  # issue-676
    pdf = FPDF()
    pdf.set_font("helvetica")
    pdf.set_section_title_styles(
        level0=TitleStyle(font_size_pt=28, l_margin=10), level1=TitleStyle()
    )
    pdf.add_page()
    pdf.start_section("Title")
    pdf.start_section("Subtitle", level=1)
    assert_pdf_equal(pdf, HERE / "toc_without_font_style.pdf", tmp_path)


def test_toc_with_font_style_override_bold(tmp_path):  # issue-1072
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B")
    pdf.set_section_title_styles(TitleStyle("Helvetica", "", 20, (0, 0, 0)))
    pdf.start_section("foo")
    assert_pdf_equal(pdf, HERE / "toc_with_font_style_override_bold.pdf", tmp_path)


def test_toc_with_table(tmp_path):  # issue-1079
    def render_toc_with_table(pdf: FPDF, outline: list):
        pdf.set_font(size=20)
        with pdf.table([[x.name, str(x.page_number)] for x in outline]):
            pass

    pdf = FPDF()
    pdf.set_font(family="helvetica", style="", size=30)
    pdf.add_page()
    pdf.insert_toc_placeholder(render_toc_function=render_toc_with_table, pages=4)
    for i in range(60):
        pdf.start_section(name=str(i), level=0)
        pdf.cell(text=str(i))
        pdf.ln()
    assert_pdf_equal(pdf, HERE / "toc_with_table.pdf", tmp_path)


def test_toc_with_right_aligned_page_numbers(tmp_path):
    def render_toc_with_right_aligned_page_numbers(pdf, outline):
        pdf.set_font("Helvetica", size=16)
        for section in outline:
            link = pdf.add_link(page=section.page_number)
            pdf.cell(
                text=f'{" " * section.level * 2} {section.name}',
                link=link,
                new_x="LEFT",
            )
            pdf.cell(text=f"{section.page_number}", link=link, w=pdf.epw, align="R")
            pdf.ln()

    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    pdf.add_page()
    pdf.insert_toc_placeholder(render_toc_with_right_aligned_page_numbers)
    insert_test_content(pdf)
    assert_pdf_equal(pdf, HERE / "toc_with_right_aligned_page_numbers.pdf", tmp_path)


def p(pdf, text, **kwargs):
    "Inserts a paragraph"
    pdf.multi_cell(
        w=pdf.epw,
        h=pdf.font_size,
        text=text,
        new_x="LMARGIN",
        new_y="NEXT",
        **kwargs,
    )


def insert_test_content(pdf):
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

    pdf.start_section("Title 1")
    pdf.start_section("Subtitle 1.1", level=1)
    p(
        pdf,
        (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
            " sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        ),
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
