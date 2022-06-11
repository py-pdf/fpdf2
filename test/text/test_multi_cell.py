from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM


HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"

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

    doc.multi_cell(
        w=144,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[:29],
        new_x="RIGHT",
        new_y="NEXT",
    )
    doc.multi_cell(
        w=180,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[29:60],
        new_x="LEFT",
        new_y="NEXT",
    )
    doc.multi_cell(
        w=144,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[60:90],
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[0:30],
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[31:60],
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[61:90],
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 5,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[91:120],
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1)
    doc.cell(w=1, h=LINE_HEIGHT, new_x="LEFT", new_y="NEXT")
    doc.multi_cell(
        w=144,
        h=LINE_HEIGHT,
        border=1,
        txt=LOREM_IPSUM[30:90],
        new_x="LEFT",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 2,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x="LEFT",
        new_y="NEXT",
    )
    doc.cell(
        w=72 * 2,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x="LEFT",
        new_y="NEXT",
    )

    assert_pdf_equal(
        doc, HERE / "ln_positioning_and_page_breaking_for_multicell.pdf", tmp_path
    )


def test_multi_cell_border_thickness(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.set_line_width(3)
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Lorem")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="ipsum")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="nostrud")
    assert_pdf_equal(doc, HERE / "multi_cell_border_thickness.pdf", tmp_path)


def test_multi_cell_ln_1(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(
        w=100,
        h=LINE_HEIGHT,
        border=1,
        txt="Lorem ipsum",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    doc.multi_cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_1.pdf", tmp_path)


def test_multi_cell_ln_3(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="Lorem", new_x="RIGHT", new_y="TOP"
    )
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="ipsum", new_x="RIGHT", new_y="TOP"
    )
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut", new_x="RIGHT", new_y="TOP")
    doc.multi_cell(
        w=45, h=LINE_HEIGHT, border=1, txt="nostrud", new_x="RIGHT", new_y="TOP"
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
                new_x="RIGHT",
                new_y="TOP",
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
                    new_x="RIGHT",
                    new_y="TOP",
                    max_line_height=pdf.font_size,
                )
            pdf.ln(line_height)
    assert_pdf_equal(
        pdf, HERE / "test_multi_cell_table_with_automatic_page_break.pdf", tmp_path
    )


def test_multi_cell_justified_with_unicode_font(tmp_path):  # issue 118
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVu", "", 14)
    text = 'Justified line containing "()" that is long enough to trigger wrapping and a line jump'
    pdf.multi_cell(w=0, h=8, txt=text, new_x="LMARGIN", new_y="NEXT")
    assert_pdf_equal(
        pdf, HERE / "test_multi_cell_justified_with_unicode_font.pdf", tmp_path
    )


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
        pdf.multi_cell(20, new_x="RIGHT", new_y="TOP", txt=str(i))
    pdf.ln(10)
    for i in range(1, 5):
        pdf.multi_cell(20, new_x="RIGHT", new_y="TOP", txt=str(i) if i > 2 else "")
    assert_pdf_equal(pdf, HERE / "multi_cell_with_empty_contents.pdf", tmp_path)


def test_multicell_newpos_badinput():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(ValueError):
        with pytest.warns(DeprecationWarning):
            pdf.multi_cell(0, ln=5)
    with pytest.raises(TypeError):
        pdf.multi_cell(0, new_x=5)
    with pytest.raises(TypeError):
        pdf.multi_cell(0, new_y=None)


def test_multi_cell_j_paragraphs(tmp_path):  # issue 364
    pdf = FPDF(format="A5")
    pdf.add_page()
    pdf.add_font("DejaVu", "", HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVu", "", 14)
    pdf.set_margins(34, 55, 34)
    pdf.set_auto_page_break(auto=True, margin=55)
    # pylint: disable=line-too-long
    text = """« Jadis, si je me souviens bien, ma vie était un festin où s’ouvraient tous les cœurs, où tous les vins coulaient.

Un soir, j’ai assis la Beauté sur mes genoux. — Et je l’ai trouvée amère. — Et je l’ai injuriée.

Je me suis armé contre la justice.

Je me suis enfui. Ô sorcières, ô misère, ô haine, c’est à vous que mon trésor a été confié !

Je parvins à faire s’évanouir dans mon esprit toute l’espérance humaine. Sur toute joie pour l’étrangler j’ai fait le bond sourd de la bête féroce.

J’ai appelé les bourreaux pour, en périssant, mordre la crosse de leurs fusils. J’ai appelé les fléaux, pour m’étouffer avec le sable, le sang. Le malheur a été mon dieu. Je me suis allongé dans la boue. Je me suis séché à l’air du crime. Et j’ai joué de bons tours à la folie."""

    pdf.multi_cell(w=0, h=None, txt=text, align="J")
    assert_pdf_equal(pdf, HERE / "multi_cell_j_paragraphs.pdf", tmp_path)


def test_multi_cell_font_leakage(tmp_path):  # Issue #359
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", style="B", fname=FONTS_DIR / "Roboto-Bold.ttf")
    pdf.set_font("Roboto", "", 12)

    pdf.multi_cell(0, txt="xyz **abcde**", markdown=True)
    pdf.ln()
    pdf.set_font("Roboto", "", 12)
    pdf.multi_cell(0, txt="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    pdf.ln()
    pdf.ln()
    pdf.multi_cell(0, txt="xyz **abcde** ", markdown=True)
    pdf.ln()
    pdf.set_font("Roboto", "", 12)
    pdf.multi_cell(0, txt="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert_pdf_equal(pdf, HERE / "multi_cell_font_leakage.pdf", tmp_path)


def test_multi_cell_with_zero_horizontal_space():  # issue #389
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(w=0, h=5, txt="test")
    with pytest.raises(FPDFException):
        pdf.multi_cell(w=0, h=5, txt="test")


def test_multi_cell_with_limited_horizontal_space():  # issue #389
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(w=pdf.epw - 2 * pdf.c_margin - 1, h=5, txt="test")
    assert pdf.x == pdf.l_margin + pdf.epw - 2 * pdf.c_margin - 1
    with pytest.raises(FPDFException):
        pdf.multi_cell(w=0, h=5, txt="test")


def test_multi_cell_trailing_nl(tmp_path):  # issue #455
    """Each multi_line() call triggers a line break at the end."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    lines = ["Hello\n", "Sweet\n", "World\n"]
    for line in lines:
        pdf.multi_cell(200, txt=line)
    pdf.cell(txt="end_mmc")
    pdf.ln(50)
    pdf.multi_cell(200, txt="".join(lines))
    pdf.cell(txt="end_mc")
    assert_pdf_equal(pdf, HERE / "multi_cell_trailing_nl.pdf", tmp_path)
