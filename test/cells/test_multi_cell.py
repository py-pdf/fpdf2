from pathlib import Path

import fpdf
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
    doc = fpdf.FPDF(format="letter", unit="pt")
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

    doc.multi_cell(w=144, h=LINE_HEIGHT, border=1, txt=text[:29], ln=0)
    doc.multi_cell(w=180, h=LINE_HEIGHT, border=1, txt=text[29:60], ln=2)
    doc.multi_cell(w=144, h=LINE_HEIGHT, border=1, txt=text[60:90], ln=1)
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1, ln=1, txt=text[0:30])
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1, ln=1, txt=text[31:60])
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1, ln=1, txt=text[61:90])
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1, ln=1, txt=text[91:120])
    doc.cell(w=72 * 5, h=LINE_HEIGHT, border=1)
    doc.cell(w=1, h=LINE_HEIGHT, ln=2)
    doc.multi_cell(w=144, h=LINE_HEIGHT, border=1, txt=text[30:90], ln=2)
    doc.cell(w=72 * 2, h=LINE_HEIGHT, border=1, ln=2, txt="Lorem ipsum")
    doc.cell(w=72 * 2, h=LINE_HEIGHT, border=1, ln=2, txt="Lorem ipsum")

    assert_pdf_equal(
        doc, HERE / "ln_positioning_and_page_breaking_for_multicell.pdf", tmp_path
    )


def test_multi_cell_ln_0(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Lorem")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="ipsum")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, txt="nostrud")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_0.pdf", tmp_path)


def test_multi_cell_ln_1(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(w=100, h=LINE_HEIGHT, border=1, txt="Lorem ipsum", ln=1)
    doc.multi_cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_1.pdf", tmp_path)


def test_multi_cell_ln_3(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=TEXT_SIZE)
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, ln=3, txt="Lorem")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, ln=3, txt="ipsum")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, ln=3, txt="Ut")
    doc.multi_cell(w=45, h=LINE_HEIGHT, border=1, ln=3, txt="nostrud")
    assert_pdf_equal(doc, HERE / "multi_cell_ln_3.pdf", tmp_path)


def test_multi_cell_ln_3_table(tmp_path):
    """
    Test rendering of a table with multi-lines cell contents
    cf. https://github.com/PyFPDF/fpdf2/issues/63
    """
    pdf = fpdf.FPDF()
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
                ln=3,
                max_line_height=pdf.font_size,
            )
        pdf.ln(line_height)
    assert_pdf_equal(pdf, HERE / "multi_cell_ln_3_table.pdf", tmp_path)


def test_multi_cell_table_unbreakable(tmp_path):  # issue 111
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for i in range(5):  # repeat table 5 times
        with pdf.unbreakable() as pdf:
            for row in TABLE_DATA:
                for datum in row:
                    pdf.multi_cell(
                        col_width, line_height, f"{datum} ({i})", border=1, ln=3
                    )
                pdf.ln(line_height)
        pdf.ln(line_height * 2)
    assert_pdf_equal(pdf, HERE / "multi_cell_table_unbreakable.pdf", tmp_path)


def test_multi_cell_justified_with_unicode_font(tmp_path):  # issue 118
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(
        "DejaVu", "", HERE / "../end_to_end_legacy/charmap/DejaVuSans.ttf", uni=True
    )
    pdf.set_font("DejaVu", "", 14)
    text = 'Justified line containing "()" that is long enough to trigger wrapping and a line jump'
    pdf.multi_cell(w=0, h=8, txt=text, ln=1)
    assert_pdf_equal(
        pdf, HERE / "test_multi_cell_justified_with_unicode_font.pdf", tmp_path
    )


## Code used to create test
# doc = fpdf.FPDF(format = 'letter', unit = 'pt')
# set_doc_date_0(doc)
# doc.add_page()

# line_height = TEXT_SIZE * spacing
# doc.set_font('helvetica', size=TEXT_SIZE)
# text = ('Lorem ipsum Ut nostrud irure reprehenderit anim nostrud dolore sed '
#         'ut Excepteur dolore ut sunt irure consectetur tempor eu tempor '
#         'nostrud dolore sint exercitation aliquip velit ullamco esse dolore '
#         'mollit ea sed voluptate commodo amet eiusmod incididunt Excepteur '
#         'Excepteur officia est ea dolore sed id in cillum incididunt quis ex '
#         'id aliqua ullamco reprehenderit cupidatat in quis pariatur ex et '
#         'veniam consectetur et minim minim nulla ea in quis Ut in '
#         'consectetur cillum aliquip pariatur qui quis sint reprehenderit '
#         'anim incididunt laborum dolor dolor est dolor fugiat ut officia do '
#         'dolore deserunt nulla voluptate officia mollit elit consequat ad '
#         'aliquip non nulla dolor nisi magna consectetur anim sint officia '
#         'sit tempor anim do laboris ea culpa eu veniam sed cupidatat in anim '
#         'fugiat culpa enim Ut cillum in exercitation magna nostrud aute '
#         'proident laboris est ullamco nulla occaecat nulla proident '
#         'consequat in ut labore non sit id cillum ut ea quis est ut dolore '
#         'nisi aliquip aute pariatur ullamco ut cillum Duis nisi elit sit '
#         'cupidatat do Ut aliqua irure sunt sunt proident sit aliqua in '
#         'dolore Ut in sint sunt exercitation aliquip elit velit dolor nisi ')


# # ln = 0: to the right
# doc.multi_cell(w = 144, h = LINE_HEIGHT, border = 1, txt = text[:29],
#                fill = 0, link = '', ln = 0)

# # ln = 2: below last item (left and down)
# doc.multi_cell(w = 180, h = LINE_HEIGHT, border = 1, txt = text[29:60],
#                fill = 0, link = '', ln = 2)

# # ln = 1: to new line, left margin
# doc.multi_cell(w = 144, h = LINE_HEIGHT, border = 1, txt = text[60:90],
#                fill = 0, link = '', ln = 1)

# doc.cell(w = 72 * 5, h = LINE_HEIGHT, border = 1, ln = 1, txt = text[0:30])
# doc.cell(w = 72 * 5, h = LINE_HEIGHT, border = 1, ln = 1, txt = text[31:60])
# doc.cell(w = 72 * 5, h = LINE_HEIGHT, border = 1, ln = 1, txt = text[61:90])
# doc.cell(w = 72 * 5, h = LINE_HEIGHT, border = 1, ln = 1, txt = text[91:120])

# # move right
# doc.cell(w = 72 * 5, h = LINE_HEIGHT, border = 1, txt = '')
# # move down
# doc.cell(w = 1, h = LINE_HEIGHT, border = 0, ln = 2, txt = '')

# doc.multi_cell(w = 144, h = LINE_HEIGHT, border = 1, txt = text[30:90],
#                fill = 0, link = '', ln = 2)
