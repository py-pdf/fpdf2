from pathlib import Path

import pytest

from fpdf import FPDF, TextStyle, TitleStyle, errors
from fpdf.outline import TableOfContents

from test.conftest import LOREM_IPSUM, assert_pdf_equal


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
        TextStyle(
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


def test_2_pages_outline_with_deprecated_TitleStyle(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica")
    with pytest.warns(DeprecationWarning):
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
            self.set_font(size=12)
            for section in outline:
                self.ln()
                self.cell(text=section.name)

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", style="I", size=8)
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
        level0=TextStyle(font_size_pt=28, l_margin=10), level1=TextStyle()
    )
    pdf.add_page()
    pdf.start_section("Title")
    pdf.start_section("Subtitle", level=1)
    assert_pdf_equal(pdf, HERE / "toc_without_font_style.pdf", tmp_path)


def test_toc_with_font_style_override_bold(tmp_path):  # issue-1072
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B")
    pdf.set_section_title_styles(
        TextStyle("Helvetica", font_size_pt=20, color=(0, 0, 0))
    )
    pdf.start_section("foo")
    assert_pdf_equal(pdf, HERE / "toc_with_font_style_override_bold1.pdf", tmp_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B")
    pdf.set_section_title_styles(
        TextStyle("Helvetica", font_style="", font_size_pt=20, color=(0, 0, 0))
    )
    pdf.start_section("foo")
    assert_pdf_equal(pdf, HERE / "toc_with_font_style_override_bold2.pdf", tmp_path)


def test_toc_without_font_style_with_deprecated_TitleStyle(tmp_path):
    pdf = FPDF()
    pdf.set_font("helvetica")
    with pytest.warns(DeprecationWarning):
        pdf.set_section_title_styles(
            level0=TitleStyle(font_size_pt=28, l_margin=10), level1=TitleStyle()
        )
    pdf.add_page()
    pdf.start_section("Title")
    pdf.start_section("Subtitle", level=1)
    assert_pdf_equal(pdf, HERE / "toc_without_font_style.pdf", tmp_path)


def test_toc_with_font_style_override_bold_with_deprecated_TitleStyle(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B")
    with pytest.warns(DeprecationWarning):
        pdf.set_section_title_styles(
            TitleStyle("Helvetica", font_size_pt=20, color=(0, 0, 0))
        )
    pdf.start_section("foo")
    assert_pdf_equal(pdf, HERE / "toc_with_font_style_override_bold1.pdf", tmp_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B")
    with pytest.warns(DeprecationWarning):
        pdf.set_section_title_styles(
            TitleStyle("Helvetica", font_style="", font_size_pt=20, color=(0, 0, 0))
        )
    pdf.start_section("foo")
    assert_pdf_equal(pdf, HERE / "toc_with_font_style_override_bold2.pdf", tmp_path)


def test_toc_with_table(tmp_path):  # issue-1079
    def render_toc_with_table(pdf: FPDF, outline: list):
        pdf.set_font(size=20)
        with pdf.table([[x.name, str(x.page_number)] for x in outline]):
            pass

    pdf = FPDF()
    pdf.set_font(family="helvetica", size=30)
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
        TextStyle(
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
        TextStyle(
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


def test_insert_toc_placeholder_with_last_page_in_landscape(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.set_y(50)
    pdf.set_font(size=40)
    p(pdf, "Doc Title", align="C")
    pdf.set_font(size=12)
    pdf.insert_toc_placeholder(render_toc)
    insert_test_content(pdf)
    pdf.add_page(orientation="L")
    pdf.start_section("Title 3")
    p(pdf, text="Nullam tempus magna quam, ac dictum neque blandit quis.")
    assert_pdf_equal(
        pdf, HERE / "insert_toc_placeholder_with_last_page_in_landscape.pdf", tmp_path
    )


def test_toc_extra_pages_with_labels(tmp_path):
    file_content = [
        {
            "name": "Chapter 1: The Origins of Procrastination",
            "level": 0,
            "paragraphs": 1,
        },
        {
            "name": "1.1 A Brief History of Putting Things Off",
            "level": 1,
            "paragraphs": 3,
        },
        {
            "name": "1.1.1 Ancient Procrastinators: Pharaohs and Philosophers",
            "level": 2,
            "paragraphs": 3,
        },
        {
            "name": "1.1.2 Renaissance Slacking: Michelangelo's 4-Year Ceiling Break",
            "level": 2,
            "paragraphs": 2,
        },
        {
            "name": "1.2 Famous Procrastinators Through Time",
            "level": 1,
            "paragraphs": 2,
        },
        {"name": "1.2.1 The Tale of Last-Minute Da Vinci", "level": 2, "paragraphs": 3},
        {
            "name": "1.2.2 Procrastination in the Age of the Internet",
            "level": 2,
            "paragraphs": 4,
        },
        {
            "name": "Chapter 2: The Science Behind Delaying Everything",
            "level": 0,
            "paragraphs": 1,
        },
        {"name": "2.1 Why We Procrastinate", "level": 1, "paragraphs": 2},
        {
            "name": "2.1.1 The Pleasure Principle vs. Deadline Panic",
            "level": 2,
            "paragraphs": 2,
        },
        {
            "name": "2.1.2 Brain Chemistry: Dopamine's Role in Putting Off Tasks",
            "level": 2,
            "paragraphs": 3,
        },
        {"name": "2.2 The Types of Procrastinators", "level": 1, "paragraphs": 2},
        {"name": "2.2.1 The Creative Avoider", "level": 2, "paragraphs": 4},
        {"name": "2.2.2 The Perfectionist Delayer", "level": 2, "paragraphs": 2},
        {"name": "2.2.3 The Professional Postponer", "level": 2, "paragraphs": 3},
        {
            "name": "Chapter 3: Procrastination Techniques and Mastery",
            "level": 0,
            "paragraphs": 1,
        },
        {
            "name": "3.1 Strategies for Effective Procrastination",
            "level": 1,
            "paragraphs": 2,
        },
        {
            "name": '3.1.1 The 10-Minute "Break" That Lasts an Hour',
            "level": 2,
            "paragraphs": 1,
        },
        {
            "name": "3.1.2 Productive Procrastination: Cleaning When You Should be Working",
            "level": 2,
            "paragraphs": 2,
        },
        {"name": "3.2 Advanced Delaying Techniques", "level": 1, "paragraphs": 1},
        {
            "name": '3.2.1 The "I\'ll Start After Lunch" Maneuver',
            "level": 2,
            "paragraphs": 2,
        },
        {"name": "3.2.2 The Art of Endless List-Making", "level": 2, "paragraphs": 3},
        {"name": "3.2.3 The Social Media Rabbit Hole", "level": 2, "paragraphs": 5},
        {
            "name": "Chapter 4: Consequences of Procrastination (That We'll Worry About Later)",
            "level": 0,
            "paragraphs": 1,
        },
        {
            "name": "4.1 What Happens When You Put Things Off",
            "level": 1,
            "paragraphs": 2,
        },
        {"name": "4.1.1 Stress Levels and Sudden Panics", "level": 2, "paragraphs": 3},
        {
            "name": "4.1.2 Creative Excuses for Deadline Extensions",
            "level": 2,
            "paragraphs": 4,
        },
        {
            "name": "4.2 Real-World Examples of Procrastination Fails",
            "level": 1,
            "paragraphs": 3,
        },
        {"name": "4.2.1 The Last-Minute Report Disaster", "level": 2, "paragraphs": 4},
        {"name": "4.2.2 The All-Nighter Presentation", "level": 2, "paragraphs": 3},
        {
            "name": "Chapter 5: Embracing Procrastination as a Lifestyle",
            "level": 0,
            "paragraphs": 1,
        },
        {"name": "5.1 Procrastination as a Philosophy", "level": 1, "paragraphs": 2},
        {"name": "5.1.1 The Zen of Doing It Tomorrow", "level": 2, "paragraphs": 2},
        {"name": "5.1.2 Practicing Mindful Delay", "level": 2, "paragraphs": 3},
        {
            "name": (
                "5.1.3 An Incredibly Long and Detailed Guide to Procrastination Tools and Techniques "
                "that Every Expert Procrastinator Should Know, Including but Not Limited to Avoidance Strategies, "
                "Deadline Extensions, and Perfecting the Art of Doing Absolutely Nothing While Looking Busy"
            ),
            "level": 2,
            "paragraphs": 5,
        },
        {"name": "5.2 The Future of Procrastination", "level": 1, "paragraphs": 2},
        {"name": "5.2.1 Delaying with AI Assistance", "level": 2, "paragraphs": 3},
        {
            "name": "5.2.2 The Rise of Procrastination Apps and Tools",
            "level": 2,
            "paragraphs": 2,
        },
    ]

    def footer():
        if pdf.page == 1:
            return
        pdf.set_y(pdf.h - 10)
        pdf.cell(text=pdf.get_page_label(), center=True)

    for test_number in range(3):

        pdf = FPDF()
        pdf.footer = footer

        pdf.add_page()
        pdf.set_font("helvetica", "", 60)
        pdf.cell(w=pdf.epw, text="TITLE", align="C")

        pdf.set_font("helvetica", "", 12)

        pdf.set_section_title_styles(
            level0=TextStyle(
                font_family="helvetica",
                font_style="B",
                font_size_pt=16,
                color="#00316e",
                b_margin=10,
            ),
            level1=TextStyle(
                font_family="helvetica",
                font_style="B",
                font_size_pt=14,
                t_margin=2.5,
                b_margin=5,
            ),
            level2=TextStyle(
                font_family="helvetica",
                font_style="I",
                font_size_pt=14,
                t_margin=2.5,
                b_margin=5,
            ),
        )

        if test_number == 0:
            # Test with a standard table of contents
            pdf.add_page(label_style="r")
            pdf.start_section("Table of Contents 1", level=0)
            toc = TableOfContents()
            pdf.insert_toc_placeholder(toc.render_toc, allow_extra_pages=True)

        if test_number == 1:
            # Test with a ToC that has a different style using a ttf font
            pdf.add_page(label_style="R")
            pdf.start_section("Table of Contents 2", level=0)
            pdf.multi_cell(
                w=pdf.epw,
                text="This is a second table of contents where a custom font is used for the ToC only.",
                new_x="lmargin",
                new_y="next",
            )
            pdf.ln()
            pdf.multi_cell(
                w=pdf.epw,
                text="Also adding extra lines to test the ToC starting renderening from the position the function is invoked.",
                new_x="lmargin",
                new_y="next",
            )
            pdf.ln()
            pdf.ln()
            pdf.add_font(
                family="Quicksand",
                style="",
                fname=HERE.parent / "fonts" / "Quicksand-Regular.otf",
            )
            toc = TableOfContents()
            toc.text_style = TextStyle(
                font_family="Quicksand", font_style="", font_size_pt=14
            )
            pdf.insert_toc_placeholder(toc.render_toc, allow_extra_pages=True)

        if test_number == 2:
            # Test using the section styles on the ToC
            pdf.add_page(label_style="a")
            pdf.start_section("Table of Contents 3", level=0)
            pdf.multi_cell(
                w=pdf.epw,
                text="This is a third table of contents using the same style as the sections.",
                new_x="lmargin",
                new_y="next",
            )
            pdf.ln()
            pdf.ln()
            toc = TableOfContents()
            toc.use_section_title_styles = True
            pdf.insert_toc_placeholder(toc.render_toc, allow_extra_pages=True)

        pdf.set_page_label(label_style="D")
        for index, content in enumerate(file_content):
            if content["level"] == 0 and index > 0:
                pdf.add_page()
            pdf.start_section(content["name"], level=content["level"])
            for _ in range(content["paragraphs"]):
                pdf.multi_cell(
                    w=pdf.epw, text=LOREM_IPSUM, new_x="lmargin", new_y="next"
                )
                pdf.ln()

        assert_pdf_equal(pdf, HERE / f"toc_with_extra_page_{test_number}.pdf", tmp_path)


def test_page_label():
    pdf = FPDF()

    # Test with no label style, prefix, or starting number (default behavior)
    pdf.add_page(label_style=None, label_prefix=None, label_start=None)
    assert pdf.get_page_label() == "1"
    pdf.add_page()
    assert pdf.get_page_label() == "2"

    # Test decimal numerals with no prefix and starting from 1
    pdf.add_page(label_style="D", label_prefix=None, label_start=1)
    assert pdf.get_page_label() == "1"
    pdf.add_page()
    assert pdf.get_page_label() == "2"

    # Test decimal numerals with a prefix and starting from 67
    pdf.add_page(label_style="D", label_prefix="A-", label_start=67)
    assert pdf.get_page_label() == "A-67"
    pdf.add_page()
    assert pdf.get_page_label() == "A-68"

    # Test lowercase Roman numerals starting from 1
    pdf.add_page(label_style="r", label_prefix=None, label_start=1)
    assert pdf.get_page_label() == "i"
    pdf.add_page()
    assert pdf.get_page_label() == "ii"

    # Test uppercase Roman numerals starting from 10 with prefix
    pdf.add_page(label_style="R", label_prefix="Preface-", label_start=10)
    assert pdf.get_page_label() == "Preface-X"
    pdf.add_page()
    assert pdf.get_page_label() == "Preface-XI"

    # Test uppercase letters starting from 1
    pdf.add_page(label_style="A", label_prefix=None, label_start=1)
    assert pdf.get_page_label() == "A"
    pdf.add_page()
    assert pdf.get_page_label() == "B"
    pdf.add_page()
    assert pdf.get_page_label() == "C"

    # Test uppercase letters with a prefix and starting beyond Z
    pdf.add_page(label_style="A", label_prefix="Appendix-", label_start=26)
    assert pdf.get_page_label() == "Appendix-Z"
    pdf.add_page()
    assert pdf.get_page_label() == "Appendix-AA"
    pdf.add_page()
    assert pdf.get_page_label() == "Appendix-AB"

    # Test lowercase letters starting from 1
    pdf.add_page(label_style="a", label_prefix=None, label_start=1)
    assert pdf.get_page_label() == "a"
    pdf.add_page()
    assert pdf.get_page_label() == "b"
    pdf.add_page()
    assert pdf.get_page_label() == "c"

    # Test lowercase letters with prefix and starting beyond z
    pdf.add_page(label_style="a", label_prefix="Sec-", label_start=26)
    assert pdf.get_page_label() == "Sec-z"
    pdf.add_page()
    assert pdf.get_page_label() == "Sec-aa"
    pdf.add_page()
    assert pdf.get_page_label() == "Sec-ab"
