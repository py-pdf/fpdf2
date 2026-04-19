from pathlib import Path

import fpdf
from fpdf.enums import MethodReturnValue
from test.conftest import assert_pdf_equal

import pytest

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_multi_cell_markdown(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor amet, **consectetur adipiscing** elit,"
        " sed do eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown.pdf", tmp_path)


def test_multi_cell_markdown_strikethrough(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    pdf.multi_cell(w=pdf.epw, text="~~strikethrough~~", markdown=True)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_strikethrough.pdf", tmp_path)


def test_multi_cell_markdown_escaped(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum \\ dolor amet, \\**consectetur adipiscing\\** elit,"
        " sed do eiusmod \\\\__tempor incididunt\\\\__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_escaped.pdf", tmp_path)


def test_multi_cell_markdown_with_ttf_fonts(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_ttf_fonts.pdf", tmp_path)


def test_multi_cell_markdown_with_ttf_fonts_escaped(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum \\ dolor, \\**consectetur adipiscing\\** elit,"
        " eiusmod \\\\__tempor incididunt\\\\__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_with_ttf_fonts_escaped.pdf", tmp_path
    )


def test_multi_cell_markdown_missing_ttf_font():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(fname=FONTS_DIR / "Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular", size=60)
    with pytest.raises(fpdf.FPDFException) as error:
        pdf.multi_cell(w=pdf.epw, text="**Lorem Ipsum**", markdown=True)
    expected_msg = "Undefined font: roboto-regularB - Use built-in fonts or FPDF.add_font() beforehand"
    assert str(error.value) == expected_msg


def test_multi_cell_markdown_with_fill_color(tmp_path):  # issue 348
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=10)
    pdf.set_fill_color(255, 0, 0)
    pdf.multi_cell(
        50, markdown=True, text="aa bb cc **dd ee dd ee dd ee dd ee dd ee dd ee**"
    )
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_fill_color.pdf", tmp_path)


def test_multi_cell_markdown_justified(tmp_path):  # issue 327
    pdf = fpdf.FPDF()
    pdf.add_page()
    for font in ("Helvetica", "Courier"):
        pdf.set_font(family=font, size=12)
        pdf.set_y(pdf.y + 3)
        pdf.multi_cell(
            190,
            markdown=True,
            align="J",
            text=(
                "Lorem **ipsum** dolor sit amet, **consectetur** adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna "
                "aliqua. Ut enim ad minim veniam, __quis__ nostrud exercitation "
                "ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
                "aute irure dolor in reprehenderit in voluptate velit esse cillum "
                "dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
                "cupidatat non proident, sunt in culpa qui officia deserunt "
                "mollit anim id est laborum."
            ),
        )
        pdf.set_x(10)
        pdf.set_y(pdf.y + 5)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_justified.pdf", tmp_path)


def test_multi_cell_markdown_link(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
    )
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link.pdf", tmp_path)


def test_multi_cell_markdown_link_dry_run(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    assert len(pdf.pages[1].annots) == 0

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 0

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 1

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 1

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 2

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_dry_run.pdf", tmp_path)


def test_multi_cell_markdown_unordered_list(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = (
        "Shopping list:\n"
        "* Apples\n"
        "- **Bananas**\n"
        "+ __Cherries__\n"
        "\n"
        "End of list."
    )
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_unordered_list.pdf", tmp_path)


def test_multi_cell_markdown_unordered_list_ttf(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=12)
    text = (
        "Shopping list:\n"
        "* Apples\n"
        "- **Bananas**\n"
        "+ __Cherries__\n"
        "\n"
        "End of list."
    )
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_unordered_list_ttf.pdf", tmp_path)


def test_multi_cell_markdown_consecutive_links(tmp_path):
    link1 = "[fpdf2 github](https://github.com/py-pdf/fpdf2)"
    link2 = "[fpdf2 github Releases](https://github.com/py-pdf/fpdf2/releases)"

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s} {link2:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 2
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s}{link2:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 4
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_consecutive_links.pdf", tmp_path)


def test_multi_cell_markdown_unordered_list_border(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = "* Apples\n- **Bananas**\n+ __Cherries__"
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, border=1)
    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_unordered_list_border.pdf", tmp_path
    )


def test_multi_cell_markdown_unordered_list_fill(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.set_fill_color(200, 220, 255)
    text = "* Apples\n- **Bananas**\n+ __Cherries__"
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, fill=True)
    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_unordered_list_fill.pdf", tmp_path
    )


def test_multi_cell_markdown_unordered_list_padding(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = "* Apples\n- **Bananas**\n+ __Cherries__"
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, padding=5)
    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_unordered_list_padding.pdf", tmp_path
    )


def test_multi_cell_markdown_unordered_list_output_lines():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = "* Apples\n- **Bananas**\n+ __Cherries__"
    lines = pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True, output=MethodReturnValue.LINES
    )
    assert isinstance(lines, list)
    assert len(lines) == 3
    assert "Apples" in lines[0]
    assert "Bananas" in lines[1]
    assert "Cherries" in lines[2]
    for line in lines:
        stripped = line.lstrip()
        assert not stripped.startswith("*")
        assert not stripped.startswith("-")
        assert not stripped.startswith("+")


def test_multi_cell_markdown_unordered_list_output_lines_padding():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = "* Apples\n- **Bananas**\n+ __Cherries__"
    lines = pdf.multi_cell(
        w=pdf.epw,
        text=text,
        markdown=True,
        output=MethodReturnValue.LINES,
        padding=5,
    )
    assert isinstance(lines, list)
    assert len(lines) == 3
    assert "Apples" in lines[0]
    assert "Bananas" in lines[1]
    assert "Cherries" in lines[2]
