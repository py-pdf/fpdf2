from pathlib import Path

import fpdf
from test.utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def document_operations(doc):
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=False, link="")


def test_put_info_all(tmp_path):
    """This test tests all possible inputs to FPDF#_put_info."""
    doc = fpdf.FPDF()
    document_operations(doc)
    doc.set_title("sample title")
    doc.set_subject("sample subject")
    doc.set_author("sample author")
    doc.set_keywords("sample keywords")
    doc.set_creator("sample creator")
    assert_pdf_equal(doc, HERE / "put_info_all.pdf", tmp_path)


def test_put_info_some(tmp_path):
    """This test tests some possible inputs to FPDF#_put_info."""
    doc = fpdf.FPDF()
    document_operations(doc)
    doc.set_title("sample title")
    # doc.set_subject('sample subject')
    # doc.set_author('sample author')
    doc.set_keywords("sample keywords")
    doc.set_creator("sample creator")
    assert_pdf_equal(doc, HERE / "put_info_some.pdf", tmp_path)
