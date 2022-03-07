from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

# pylint: disable=all
text_data = (
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
)
# pylint: enable=all


def test_write_page_break(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=24)
    doc.y = 20
    doc.write(txt=text_data)
    doc.write(txt=text_data)
    assert_pdf_equal(doc, HERE / "write_page_break.pdf", tmp_path)


def test_write_soft_hyphen(tmp_path):
    s = "Donau\u00addamp\u00adfschiff\u00adfahrts\u00adgesellschafts\u00adkapitäns\u00admützen\u00adstreifen. "
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=24)
    doc.y = 20
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="B")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="I")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24)
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="B")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24, style="I")
    doc.write(txt=s)
    doc.set_font("helvetica", size=24)
    doc.write(txt=s)
    assert_pdf_equal(doc, HERE / "write_soft_hyphen.pdf", tmp_path)
