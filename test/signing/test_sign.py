from pathlib import Path


from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_sign_pkcs12(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.sign_pkcs12(HERE / "certs.p12", password=b"1234")
    assert_pdf_equal(pdf, HERE / "sign_pkcs12.pdf", tmp_path)
