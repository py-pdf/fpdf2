import fpdf
from test.utilities import assert_pdf_equal


def document_operations(doc):
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=False, link="")


class TestCatalogDisplayMode:
    """This test tests some possible inputs to FPDF#_put_info."""

    def test_put_info_all(self):
        doc = fpdf.FPDF()
        document_operations(doc)
        doc.set_title("sample title")
        doc.set_subject("sample subject")
        doc.set_author("sample author")
        doc.set_keywords("sample keywords")
        doc.set_creator("sample creator")
        assert_pdf_equal(doc, "put_info_all.pdf")

    def test_put_info_some(self):
        doc = fpdf.FPDF()
        document_operations(doc)
        doc.set_title("sample title")
        # doc.set_subject('sample subject')
        # doc.set_author('sample author')
        doc.set_keywords("sample keywords")
        doc.set_creator("sample creator")
        assert_pdf_equal(doc, "put_info_some.pdf")
