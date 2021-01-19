import unittest

import fpdf
from test.utilities import assert_pdf_equal

# python -m unittest test.cell_multi_cell_refactor.cell


class CellTest(unittest.TestCase):
    def test_ln_positioning_and_page_breaking_for_cell(self):
        doc = fpdf.FPDF(format="letter", unit="pt")
        doc.add_page()

        my_text_size = 36
        doc.set_font("helvetica", size=my_text_size)
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
                h=my_text_size * 1.5,
                border=1,
                ln=2,
                txt=text[i * 100 : i * 100 + 99],
            )

        assert_pdf_equal(
            self, doc, "test_ln_positioning_and_page_breaking_for_cell.pdf"
        )


if __name__ == "__main__":
    unittest.main()

## Code used to create this test
# doc = fpdf.FPDF(format = 'letter', unit = 'pt')
# set_doc_date_0(doc)
# doc.add_page()

# my_text_size = 36
# doc.set_font('helvetica', size=my_text_size)
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


if __name__ == "__main__":
    unittest.main()
