from pathlib import Path

import pytest

from fpdf import FPDF, XPos, YPos
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent

TEXT_SIZE, SPACING = 36, 1.15
LINE_HEIGHT = TEXT_SIZE * SPACING

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
)


def test_ln_positioning_and_page_breaking_for_multicell(tmp_path):
    doc = FPDF(format="letter", unit="pt")
    doc.add_page()

    doc.set_font("helvetica", size=TEXT_SIZE)
    text = (
        "Lorem ipsum Ut nostrud irure reprehenderit anim nostrud dolore sed "
        "ut Excepteur dolore ut sunt irure consectetur tempor eu tempor "
        "nostrud dolore sint exercitation aliquip velit ullamco esse dolore "
        "mollit ea sed voluptate commodo amet eiusmod incididunt Excepteur "
        "Excepteur officia est ea dolore sed id in cillum incididunt quis ex "
        "id aliqua ullamco reprehenderit cupidatat in quis pariatur ex et "
        "veniam consectetur et minim minim nulla ea in quis Ut in "
        "consectetur cillum aliquip pariatur qui quis sint reprehenderit "
        "anim incididunt laborum dolor dolor est dolor fugiat ut officia do "
        "dolore deserunt nulla voluptate officia mollit elit consequat ad "
        "aliquip non nulla dolor nisi magna consectetur anim sint officia "
        "sit tempor anim do laboris ea culpa eu veniam sed cupidatat in anim "
        "fugiat culpa enim Ut cillum in exercitation magna nostrud aute "
        "proident laboris est ullamco nulla occaecat nulla proident "
        "consequat in ut labore non sit id cillum ut ea quis est ut dolore "
        "nisi aliquip aute pariatur ullamco ut cillum Duis nisi elit sit "
        "cupidatat do Ut aliqua irure sunt sunt proident sit aliqua in "
        "dolore Ut in sint sunt exercitation aliquip elit velit dolor nisi "
    )

    doc.multi_cell(
        w=144, h=LINE_HEIGHT, border=1, txt=text[:29], new_x=XPos.RIGHT, new_y=YPos.NEXT
    )
    doc.multi_cell(
        w=180,
        h=LINE_HEIGHT,
        border=1,
        txt=text[29:60],
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
    )
    doc.multi_cell(
        w=144,
        h=LINE_HEIGHT,
        border=1,
        txt=text[60:90],
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=text[0:30],
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=text[31:60],
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=text[61:90],
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=text[91:120],
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1)
    doc.cell(w=1, h=LINE_HEIGHT, new_x=XPos.LEFT, new_y=YPos.NEXT)
    doc.multi_cell(
        w=144,
        h=LINE_HEIGHT,
        border=1,
        txt=text[30:90],
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 2,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
    )
    doc.cell(
        w=72 * 2,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x=XPos.LEFT,
        new_y=YPos.NEXT,
    )

    assert_pdf_equal(
        doc, HERE / "ln_positioning_and_page_breaking_for_multicell.pdf", tmp_path
    )


def test_multi_cell_ln_0(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Lorem")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="ipsum")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="nostrud")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_0.pdf", tmp_path)


def test_multi_cell_ln_1(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(
        w=100,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    doc.multi_cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_1.pdf", tmp_path)


def test_multi_cell_ln_3(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="Lorem", new_x=XPos.RIGHT, new_y=YPos.TOP
    )
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="ipsum", new_x=XPos.RIGHT, new_y=YPos.TOP
    )
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="Ut", new_x=XPos.RIGHT, new_y=YPos.TOP
    )
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="nostrud", new_x=XPos.RIGHT, new_y=YPos.TOP
    )
    assert_pdf_equal(doc, HERE / "multi_cell_ln_3.pdf", tmp_path)


def test_multi_cell_ln_3_table(tmp_path):
    """
    Test rendering of a table with multi-lines cell contents
    cf. https://github.com/PyFPDF/fpdf2/issues/63
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=10)
    line_height = pdf.font_size * 2.5
    # Set column width to 1/4 of effective page width to distribute content
    # evenly across table and page
    col_width = pdf.epw / 4
    for row in TABLE_DATA:
        for datum in row:
            pdf.multi_cell(
                col_width,
                line_height,
                str(datum),
                border=1,
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
                max_line_height=pdf.font_size,
            )
        pdf.ln(line_height)
    assert_pdf_equal(pdf, HERE / "multi_cell_ln_3_table.pdf", tmp_path)


def test_multi_cell_table_with_automatic_page_break(tmp_path):  # issue 120
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for _ in range(5):  # repeat table 5 times
        for row in TABLE_DATA:
            for datum in row:
                pdf.multi_cell(
                    col_width,
                    line_height,
                    datum,
                    border=1,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                    max_line_height=pdf.font_size,
                )
            pdf.ln(line_height)
    assert_pdf_equal(
        pdf, HERE / "test_multi_cell_table_with_automatic_page_break.pdf", tmp_path
    )


def test_multi_cell_table_unbreakable(tmp_path):  # issue 111
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for i in range(5):  # repeat table 5 times
        with pdf.unbreakable() as pdf:
            for row in TABLE_DATA:
                for datum in row:
                    pdf.multi_cell(
                        col_width,
                        line_height,
                        f"{datum} ({i})",
                        border=1,
                        new_x=XPos.RIGHT,
                        new_y=YPos.TOP,
                    )
                pdf.ln(line_height)
        pdf.ln(line_height * 2)
    assert_pdf_equal(pdf, HERE / "multi_cell_table_unbreakable.pdf", tmp_path)


def test_multi_cell_justified_with_unicode_font(tmp_path):  # issue 118
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVu", "", 14)
    text = 'Justified line containing "()" that is long enough to trigger wrapping and a line jump'
    pdf.multi_cell(w=0, h=8, txt=text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    assert_pdf_equal(
        pdf, HERE / "test_multi_cell_justified_with_unicode_font.pdf", tmp_path
    )


def test_multi_cell_table_unbreakable2(tmp_path):  # issue 120 - 2nd snippet
    table = {
        "A": "test_lin_o_00000_001",
        "B": "3",
        "C": "4",
        "D": "test_lin_o_00000",
        "E": "7",
        "F": "test_lin_o_00000",
        "G": "test_lin",
        "H": "test_lin",
    }
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20)
    pdf.set_font("Times", "B", size=7)
    line_height = pdf.font_size * 3
    col_width = pdf.epw / 8
    for header in table:
        pdf.multi_cell(
            col_width,
            line_height,
            header,
            border=1,
            new_x=XPos.RIGHT,
            new_y=YPos.TOP,
            max_line_height=pdf.font_size,
            align="C",
        )
    pdf.ln(line_height)
    pdf.set_font(style="")
    line_height = pdf.font_size * 10
    col_width = pdf.epw / 8
    for _ in range(11):
        with pdf.unbreakable():
            for cell in table.values():
                pdf.multi_cell(
                    col_width,
                    line_height,
                    cell,
                    border=1,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                    max_line_height=pdf.font_size,
                    align="C",
                )
        pdf.ln(line_height)
    assert_pdf_equal(pdf, HERE / "multi_cell_table_unbreakable2.pdf", tmp_path)


def test_multi_cell_split_only():  # discussion 314
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=TEXT_SIZE)
    text = "Lorem ipsum Ut nostrud irure reprehenderit anim nostrud dolore sed ut"
    expected = [
        "Lorem ipsum Ut nostrud irure",
        "reprehenderit anim nostrud",
        "dolore sed ut",
    ]
    assert pdf.multi_cell(w=0, h=LINE_HEIGHT, txt=text, split_only=True) == expected


def test_multi_cell_with_empty_contents(tmp_path):  # issue 349
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    for i in range(1, 5):
        pdf.multi_cell(20, new_x=XPos.RIGHT, new_y=YPos.TOP, txt=str(i))
    pdf.ln(10)
    for i in range(1, 5):
        pdf.multi_cell(
            20, new_x=XPos.RIGHT, new_y=YPos.TOP, txt=str(i) if i > 2 else ""
        )
    assert_pdf_equal(pdf, HERE / "multi_cell_with_empty_contents.pdf", tmp_path)


def test_multicell_newpos_badinput(tmp_path):  # pylint: disable=unused-argument
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(ValueError):
        with pytest.warns(DeprecationWarning):
            pdf.multi_cell(0, ln=5)
    with pytest.raises(ValueError):
        pdf.multi_cell(0, new_x=5)
    with pytest.raises(ValueError):
        pdf.multi_cell(0, new_y=None)
