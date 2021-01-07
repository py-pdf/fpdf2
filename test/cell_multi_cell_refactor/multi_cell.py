import unittest
import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..")),
)

import fpdf
from test.utilities import assert_pdf_equal

# python -m unittest test.cell_multi_cell_refactor.multi_cell


class MCRefactorTest(unittest.TestCase):
    def test_ln_positioning_and_page_breaking_for_multicell(self):
        doc = fpdf.FPDF(format="letter", unit="pt")
        doc.add_page()

        my_text_size = 36
        spacing = 1.15
        line_height = my_text_size * spacing
        doc.set_font("Arial", size=my_text_size)
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
            w=144, h=line_height, border=1, txt=text[:29], fill=0, link="", ln=0
        )
        doc.multi_cell(
            w=180, h=line_height, border=1, txt=text[29:60], fill=0, link="", ln=2
        )
        doc.multi_cell(
            w=144, h=line_height, border=1, txt=text[60:90], fill=0, link="", ln=1
        )
        doc.cell(w=72 * 5, h=line_height, border=1, ln=1, txt=text[0:30])
        doc.cell(w=72 * 5, h=line_height, border=1, ln=1, txt=text[31:60])
        doc.cell(w=72 * 5, h=line_height, border=1, ln=1, txt=text[61:90])
        doc.cell(w=72 * 5, h=line_height, border=1, ln=1, txt=text[91:120])
        doc.cell(w=72 * 5, h=line_height, border=1, txt="")
        doc.cell(w=1, h=line_height, border=0, ln=2, txt="")
        doc.multi_cell(
            w=144, h=line_height, border=1, txt=text[30:90], fill=0, link="", ln=2
        )
        doc.cell(w=72 * 2, h=line_height, border=1, ln=2, txt="Lorem ipsum")
        doc.cell(w=72 * 2, h=line_height, border=1, ln=2, txt="Lorem ipsum")

        assert_pdf_equal(
            self, doc, "test_ln_positioning_and_page_breaking_for_multicell.pdf"
        )


if __name__ == "__main__":
    unittest.main()

## Code used to create test
# doc = fpdf.FPDF(format = 'letter', unit = 'pt')
# set_doc_date_0(doc)
# doc.add_page()

# my_text_size = 36
# spacing = 1.15
# line_height = my_text_size * spacing
# doc.set_font('Arial', size=my_text_size)
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
# doc.multi_cell(w = 144, h = line_height, border = 1, txt = text[:29],
#                fill = 0, link = '', ln = 0)

# # ln = 2: below last item (left and down)
# doc.multi_cell(w = 180, h = line_height, border = 1, txt = text[29:60],
#                fill = 0, link = '', ln = 2)

# # ln = 1: to new line, left margin
# doc.multi_cell(w = 144, h = line_height, border = 1, txt = text[60:90],
#                fill = 0, link = '', ln = 1)

# doc.cell(w = 72 * 5, h = line_height, border = 1, ln = 1, txt = text[0:30])
# doc.cell(w = 72 * 5, h = line_height, border = 1, ln = 1, txt = text[31:60])
# doc.cell(w = 72 * 5, h = line_height, border = 1, ln = 1, txt = text[61:90])
# doc.cell(w = 72 * 5, h = line_height, border = 1, ln = 1, txt = text[91:120])

# # move right
# doc.cell(w = 72 * 5, h = line_height, border = 1, txt = '')
# # move down
# doc.cell(w = 1, h = line_height, border = 0, ln = 2, txt = '')

# doc.multi_cell(w = 144, h = line_height, border = 1, txt = text[30:90],
#                fill = 0, link = '', ln = 2)

# doc.cell(w = 72 * 2, h = line_height, border = 1, ln = 2, txt = 'Lorem ipsum')
# doc.cell(w = 72 * 2, h = line_height, border = 1, ln = 2, txt = 'Lorem ipsum')

# outfile = relative_path_to('output.pdf')
# doc.output(outfile)
# print(calculate_hash_of_file(outfile))
# os.unlink(outfile)
