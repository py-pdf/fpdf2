import itertools
from pathlib import Path

import fpdf
from fpdf.enums import MethodReturnValue
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
    # A reference PDF alone can accidentally bless output with no border.
    assert b"S" in pdf.pages[1].contents.split()
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
        assert isinstance(line, str)
        stripped = line.lstrip()  # pylint: disable=no-member
        assert not stripped.startswith(("* ", "- ", "+ "))


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


@pytest.mark.parametrize("marker", ["*", "-", "+"])
@pytest.mark.parametrize("padding", [10, (20, 3, 5, 7)])
def test_multi_cell_markdown_unordered_list_padding_applied_once(marker, padding):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    start_x, start_y = pdf.x, pdf.y
    plain_text = "Shopping list:\nApples\nBananas\nEnd of list."
    list_text = f"Shopping list:\n{marker} Apples\n{marker} Bananas\nEnd of list."

    pdf.multi_cell(
        w=100,
        h=5,
        text=plain_text,
        markdown=True,
        padding=padding,
        new_x="LEFT",
        new_y="NEXT",
    )
    plain_end_y = pdf.y
    pdf.set_xy(start_x, start_y)
    pdf.multi_cell(
        w=100,
        h=5,
        text=list_text,
        markdown=True,
        padding=padding,
        new_x="LEFT",
        new_y="NEXT",
    )

    # These short items do not wrap: both blocks need four lines and one padding.
    assert pdf.y == pytest.approx(plain_end_y)
    assert pdf.x == pytest.approx(start_x)


@pytest.mark.parametrize("padding", [0, 3])
def test_multi_cell_markdown_unordered_list_output_lines_preserves_height(padding):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    text = "* " + "word " * 25
    start_page, start_x, start_y = pdf.page, pdf.x, pdf.y
    original_contents = bytes(pdf.pages[1].contents)

    height = pdf.multi_cell(
        w=40,
        h=5,
        text=text,
        markdown=True,
        padding=padding,
        dry_run=True,
        output=MethodReturnValue.HEIGHT,
    )
    lines, height_with_lines = pdf.multi_cell(
        w=40,
        h=5,
        text=text,
        markdown=True,
        padding=padding,
        dry_run=True,
        output=MethodReturnValue.LINES | MethodReturnValue.HEIGHT,
    )

    assert len(lines) > 1  # Exercise wrapping within an indented list item.
    assert height_with_lines == pytest.approx(height)
    assert (pdf.page, pdf.x, pdf.y) == (start_page, start_x, start_y)
    assert bytes(pdf.pages[1].contents) == original_contents


@pytest.mark.parametrize(
    "output",
    [MethodReturnValue.HEIGHT, MethodReturnValue.HEIGHT | MethodReturnValue.LINES],
)
def test_multi_cell_markdown_unordered_list_bullet_after_page_break(output):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.set_y(pdf.page_break_trigger - 2)
    pdf.multi_cell(80, 5, "* Apples", markdown=True, output=output)
    assert pdf.page == 2
    assert b"( - )" not in pdf.pages[1].contents
    assert b"( - )" in pdf.pages[2].contents
    assert b"(Apples)" in pdf.pages[2].contents


@pytest.mark.parametrize("new_x", ["LEFT", "RIGHT", "LMARGIN"])
@pytest.mark.parametrize("new_y", ["TOP", "NEXT", "LAST"])
def test_multi_cell_markdown_unordered_list_cursor(new_x, new_y):
    positions = []
    for text in ("Apples\nBananas", "* Apples\n* Bananas"):
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.set_xy(30, 40)
        pdf.multi_cell(
            80, 5, text, markdown=True, padding=(10, 3, 5, 7), new_x=new_x, new_y=new_y
        )
        positions.append((pdf.x, pdf.y))
    assert positions[1] == pytest.approx(positions[0])


def test_multi_cell_markdown_unordered_list_empty_item():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    start_y = pdf.y
    lines = pdf.multi_cell(80, 5, "* ", markdown=True, output=MethodReturnValue.LINES)
    assert lines == [""]
    assert pdf.y == pytest.approx(start_y + 5)
    assert b"( - )" in pdf.pages[1].contents


@pytest.mark.parametrize("shaping", [False, True])
def test_multi_cell_markdown_unordered_list_continued_emphasis(shaping):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.set_text_shaping(shaping)
    lines = pdf.multi_cell(
        80,
        5,
        "* **Apples\n* Bananas**",
        markdown=True,
        dry_run=True,
        output=MethodReturnValue.LINES,
    )
    assert lines == ["**Apples**", "**Bananas**"]


@pytest.mark.parametrize("align", ["L", "C", "R", "X"])
def test_multi_cell_markdown_unordered_list_alignment(align):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.set_xy(80, 40)
    pdf.multi_cell(
        60,
        5,
        "* Apples\n* Bananas",
        markdown=True,
        align=align,
        new_x="RIGHT",
        new_y="NEXT",
    )
    assert pdf.x == pytest.approx(110 if align == "X" else 140)
    # Bullets start at the block's left edge, regardless of text alignment.
    bullet_x = (50 if align == "X" else 80) + pdf.c_margin
    prefix = f"BT {bullet_x * pdf.k:.2f} ".encode()
    bullet_commands = [
        line for line in pdf.pages[1].contents.splitlines() if b"( - )" in line
    ]
    assert len(bullet_commands) == 2
    assert all(line.startswith(prefix) for line in bullet_commands)


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


def test_multi_cell_markdown_escaped_markers_inside_link():  # issue 1847
    # Escaping markdown markers inside a link previously left the escape
    # backslashes in the rendered text, and the LINES re-serialization emitted
    # the display text verbatim, producing double-escaped output such as
    # "\**Issue\**". Both the parsed fragment and the LINES round-trip must
    # now be free of stray escape characters.
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    text = "[\\**Issue\\** 1844](https://github.com/py-pdf/fpdf2/pull/1844)"

    # The LINES re-serialization must round-trip stably without accumulating
    # additional escape characters.
    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    assert lines == ["[\\**Issue\\** 1844](https://github.com/py-pdf/fpdf2/pull/1844)"]
