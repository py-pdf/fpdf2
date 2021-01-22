from pathlib import Path

import fpdf
from test.utilities import assert_pdf_equal

TEXT_SIZE, SPACING = 36, 1.15
LINE_HEIGHT = TEXT_SIZE * SPACING


HERE = Path(__file__).resolve().parent


class TestCell:
    def test_ln_positioning_and_page_breaking_for_cell(self, tmp_path):
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
            ""
        ) * 100

        for i in range(20):
            doc.cell(
                w=72,
                h=TEXT_SIZE * 1.5,
                border=1,
                ln=2,
                txt=text[i * 100 : i * 100 + 99],
            )

        assert_pdf_equal(
            doc, HERE / "ln_positioning_and_page_breaking_for_cell.pdf", tmp_path
        )

    def test_cell_ln_0(self, tmp_path):
        doc = fpdf.FPDF()
        doc.add_page()
        doc.set_font("helvetica", size=TEXT_SIZE)
        doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="Lorem")
        doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="ipsum")
        doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="Ut")
        doc.cell(w=45, h=LINE_HEIGHT, border=1, txt="nostrud")
        assert_pdf_equal(doc, HERE / "ln_0.pdf", tmp_path)

    def test_cell_ln_1(self, tmp_path):
        """
        Validating that: "Using ln=1 is equivalent to using ln=0 and calling the `ln` method just after."
        """
        doc = fpdf.FPDF()
        doc.add_page()
        doc.set_font("helvetica", size=TEXT_SIZE)
        doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Lorem ipsum", ln=1)
        doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
        assert_pdf_equal(doc, HERE / "ln_1.pdf", tmp_path)

        doc = fpdf.FPDF()
        doc.add_page()
        doc.set_font("helvetica", size=TEXT_SIZE)
        doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Lorem ipsum")
        doc.ln()
        doc.cell(w=100, h=LINE_HEIGHT, border=1, txt="Ut nostrud irure")
        assert_pdf_equal(doc, HERE / "ln_1.pdf", tmp_path)


## Code used to create this test
# doc = fpdf.FPDF(format = 'letter', unit = 'pt')
# set_doc_date_0(doc)
# doc.add_page()

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
#         'dolore Ut in sint sunt exercitation aliquip elit velit dolor nisi '
#         '')*100
