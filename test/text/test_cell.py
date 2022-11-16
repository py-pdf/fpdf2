from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM

TEXT_SIZE, SPACING = 36, 1.15
LINE_HEIGHT = TEXT_SIZE * SPACING


HERE = Path(__file__).resolve().parent

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
)


def test_ln_positioning_and_page_breaking_for_cell(tmp_path):
    doc = FPDF(format="letter", unit="pt")
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    text = LOREM_IPSUM * 100
    for i in range(20):
        doc.cell(
            w=72,
            h=TEXT_SIZE * 1.5,
            border=1,
            new_x="LEFT",
            new_y="NEXT",
            txt=text[i * 100 : i * 100 + 99],
        )

    assert_pdf_equal(
        doc, HERE / "ln_positioning_and_page_breaking_for_cell.pdf", tmp_path
    )


def test_cell_ln_0(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="Lorem")
    doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="ipsum")
    doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut")
    doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="nostrud")
    assert_pdf_equal(doc, HERE / "ln_0.pdf", tmp_path)


def test_cell_ln_1(tmp_path):
    """
    Catch DeprecationWarning for ln=1.
    Validating that: "Using ln=1 is equivalent to using ln=0 and calling the `ln` method just after."
    """
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    with pytest.warns(DeprecationWarning):
        doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Lorem ipsum", ln=1)
    doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
    assert_pdf_equal(doc, HERE / "ln_1.pdf", tmp_path)

    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Lorem ipsum")
    doc.ln()
    doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
    assert_pdf_equal(doc, HERE / "ln_1.pdf", tmp_path)


def test_cell_table_with_pagebreak(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for i in range(4):  # repeat table 4 times
        for row in TABLE_DATA:
            for datum in row:
                pdf.cell(col_width, line_height, f"{datum} ({i})", border=1)
            pdf.ln(line_height)
        pdf.ln(line_height * 2)
    assert_pdf_equal(pdf, HERE / "cell_table_with_pagebreak.pdf", tmp_path)


def test_cell_table_unbreakable(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for i in range(5):  # repeat table 5 times
        with pdf.unbreakable() as doc:
            for row in TABLE_DATA:
                for datum in row:
                    doc.cell(col_width, line_height, f"{datum} ({i})", border=1)
                doc.ln(line_height)
        pdf.ln(line_height * 2)
    assert_pdf_equal(pdf, HERE / "cell_table_unbreakable.pdf", tmp_path)


def test_cell_without_font_set():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        pdf.cell(txt="Hello World!")
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(error.value) == expected_msg


def test_cell_without_w_nor_h(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.cell(txt="Lorem ipsum", border=1)
    pdf.set_font_size(80)
    pdf.cell(txt="Lorem ipsum", border=1)
    assert_pdf_equal(pdf, HERE / "cell_without_w_nor_h.pdf", tmp_path)


def test_cell_missing_text_or_width():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(ValueError) as error:
        pdf.cell()
    assert (
        str(error.value)
        == "A 'text_line' parameter with fragments must be provided if 'w' is None"
    )


def test_cell_centering(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=60)
    with pytest.warns(DeprecationWarning):
        pdf.cell(txt="Lorem ipsum", border=1, center=True)
    assert_pdf_equal(pdf, HERE / "cell_centering.pdf", tmp_path)


def test_cell_markdown(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=60)
    pdf.cell(txt="**Lorem** __Ipsum__ --dolor--", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown.pdf", tmp_path)


def test_cell_markdown_with_ttf_fonts(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", HERE / "../fonts/Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", HERE / "../fonts/Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", HERE / "../fonts/Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=60)
    pdf.cell(txt="**Lorem** __Ipsum__ --dolor--", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_with_ttf_fonts.pdf", tmp_path)


def test_cell_markdown_missing_ttf_font():
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(fname=HERE / "../fonts/Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular", size=60)
    with pytest.raises(FPDFException) as error:
        pdf.cell(txt="**Lorem Ipsum**", markdown=True)
    expected_msg = "Undefined font: roboto-regularB - Use built-in fonts or FPDF.add_font() beforehand"
    assert str(error.value) == expected_msg


def test_cell_markdown_bleeding(tmp_path):  # issue 241
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=60)
    pdf.cell(txt="--Lorem Ipsum dolor--", markdown=True, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(txt="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(txt="**Lorem Ipsum dolor**", markdown=True, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(txt="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(txt="__Lorem Ipsum dolor__", markdown=True, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(txt="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    assert_pdf_equal(pdf, HERE / "cell_markdown_bleeding.pdf", tmp_path)


def test_cell_markdown_right_aligned(tmp_path):  # issue 333
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=HERE / "../fonts/Roboto-Regular.ttf")
    pdf.add_font("Roboto", style="B", fname=HERE / "../fonts/Roboto-Bold.ttf")
    pdf.set_font("Roboto", size=60)
    pdf.cell(
        0,
        9,
        "**X** **X** **X** **X** **X** **X** **X** **X** **X**",
        markdown=True,
        align="R",
    )
    assert_pdf_equal(pdf, HERE / "cell_markdown_right_aligned.pdf", tmp_path)


def test_table_with_headers_on_every_page(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly

    def render_table_header():
        pdf.set_font(style="B")  # enabling bold text
        for col_name in TABLE_DATA[0]:
            pdf.cell(col_width, line_height, col_name, border=1)
        pdf.ln(line_height)
        pdf.set_font(style="")  # disabling bold text

    render_table_header()
    for _ in range(10):  # repeat data rows
        for row in TABLE_DATA[1:]:
            if pdf.will_page_break(line_height):
                render_table_header()
            for datum in row:
                pdf.cell(col_width, line_height, datum, border=1)
            pdf.ln(line_height)
    assert_pdf_equal(pdf, HERE / "table_with_headers_on_every_page.pdf", tmp_path)


def test_cell_newpos_badinput():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(ValueError):
        with pytest.warns(DeprecationWarning):
            pdf.cell(w=0, ln=5)
    with pytest.raises(TypeError):
        pdf.cell(w=0, new_x=5)
    with pytest.raises(TypeError):
        pdf.cell(w=0, new_y=None)
    with pytest.raises(ValueError):
        pdf.cell(w=0, align="J")


def test_cell_curfont_leak(tmp_path):  # issue #475
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=HERE / "../fonts/Roboto-Regular.ttf")
    pdf.add_font("Roboto", style="B", fname=HERE / "../fonts/Roboto-Bold.ttf")
    with pdf.local_context():
        pdf.set_font("Roboto", "B", 10)
        pdf.cell(txt="ABCDEFGH", new_x="LEFT", new_y="NEXT")
    pdf.set_font("Roboto", "", 10)
    pdf.cell(txt="IJKLMNOP", new_x="LEFT", new_y="NEXT")
    with pdf.local_context():
        pdf.set_font("Roboto", "B", 10)
        pdf.cell(txt="QRSTUVW", new_x="LEFT", new_y="NEXT")
    pdf.set_font("Roboto", "", 10)
    pdf.cell(txt="XYZ012abc,-", new_x="LEFT", new_y="NEXT")
    pdf.cell(txt="3,7E-05", new_x="LEFT", new_y="NEXT")
    assert_pdf_equal(pdf, HERE / "cell_curfont_leak.pdf", tmp_path)


# pylint: disable=protected-access
def test_cell_lasth(tmp_path):  # issue #601
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=18)
    pdf.set_fill_color(255, 255, 0)
    pdf.cell(w=100, txt="Hello world", fill=True)
    print(pdf._lasth)  # prints: 6.35
    pdf.ln()
    assert pdf._lasth == 6.35, f"pdf._lasth ({pdf._lasth}) != 5.35"
    pdf.set_fill_color(255, 0, 255)
    pdf.cell(w=100, txt="Hello world", h=50, fill=True)
    pdf.ln()
    assert pdf._lasth == 50, f"pdf._lasth ({pdf._lasth}) != 50 after cell(h=50)"
    pdf.set_fill_color(0, 255, 255)
    pdf.cell(w=100, txt="Hello world", fill=True)
    pdf.cell(w=100, txt="")
    pdf.ln()
    assert pdf._lasth == 6.35, f"pdf._lasth ({pdf._lasth}) != 5.35 after empty cell"
    pdf.cell(w=100, txt="Hello world", border=True)
    assert_pdf_equal(pdf, HERE / "cell_lasth.pdf", tmp_path)
