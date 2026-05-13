import itertools
from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal
from test.conftest import LOREM_IPSUM

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


def test_multi_cell_markdown_styled_link(tmp_path):
    styles = (
        ("Bold", "**"),
        ("Italics", "__"),
        ("Strikethrough", "~~"),
        ("Underline", "--"),
    )
    style_combinations = []
    for i in range(1, len(styles) + 1):
        for combo in itertools.combinations(styles, i):
            style = "-".join(c[0] for c in combo)
            marker = "".join(c[1] for c in combo)
            style_combinations.append((style, marker))

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for link_color, link_underline in itertools.product(
        (None, "#0000ff"),
        (False, True),
    ):
        pdf.MARKDOWN_LINK_COLOR = link_color
        pdf.MARKDOWN_LINK_UNDERLINE = link_underline
        for style, marker in style_combinations:
            pdf.multi_cell(
                pdf.epw,
                text=f"**Start** {marker:s}[{style:s} Link](https://github.com/py-pdf/fpdf2){marker:s} __End__",
                markdown=True,
                new_x="left",
                new_y="next",
            )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_styled_link.pdf", tmp_path)


@pytest.mark.parametrize(
    "text",
    [
        "**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2)\n__End__",
        LOREM_IPSUM
        + "\n**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2)\n__End__",
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + " **\nStart** [fpdf2 github](https://github.com/py-pdf/fpdf2)\n__End__ "
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :],
    ],
)
def test_multi_cell_markdown_dry_run_lines_output(text):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )

    # The parts of the special markdown text must be in the lines list, but not
    # in the same line
    assert any("**Start**" in line for line in lines)
    assert any(
        "[fpdf2 github](https://github.com/py-pdf/fpdf2)" in line for line in lines
    )
    assert any("__End__" in line for line in lines)
    start_line = next(i for i, line in enumerate(lines) if "**Start**" in line)
    end_line = next(i for i, line in enumerate(lines) if "__End__" in line)
    assert start_line + 1 == end_line

    parsed_text = "\n".join(lines)
    assert (
        "**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2)\n__End__"
        in parsed_text
    )


def test_multi_cell_markdown_dry_run_lines_output_print(tmp_path):
    # Test that output="LINES" keeps markdown format
    text = (
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + "\n**Start** ~~test~~ "
        + "[fpdf2 github](https://github.com/py-pdf/fpdf2) "
        + "--test--\n__End__ "
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :]
    )

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    # Normal text
    pdf.multi_cell(
        pdf.epw,
        text=text,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    pdf.ln()

    # Join text after dry run by `"\n"`
    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    pdf.multi_cell(
        pdf.epw,
        text="\n".join(lines),
        markdown=True,
        new_x="left",
        new_y="next",
    )

    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_dry_run_lines_output.pdf", tmp_path
    )


def test_multi_cell_markdown_dry_run_lines_output_escape(tmp_path):
    # Test that escaped markdown markers stay escaped
    text = (
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + "\n**Start** \\** [fpdf2 **github**](https://github.com/py-pdf/fpdf2) "
        + "\\__ \\~~ \\--\n__End__ "  # Important test underline after link
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :]
    )

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    # Normal text
    pdf.multi_cell(
        pdf.epw,
        text=text,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    pdf.ln()

    # Join text after dry run by `"\n"`
    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    pdf.multi_cell(
        pdf.epw,
        text="\n".join(lines),
        markdown=True,
        new_x="left",
        new_y="next",
    )

    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_dry_run_lines_output_escape.pdf", tmp_path
    )
