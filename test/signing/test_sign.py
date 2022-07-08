from pathlib import Path


from fpdf import FPDF
from test.conftest import assert_pdf_equal, check_signature, EPOCH


HERE = Path(__file__).resolve().parent
TRUSTED_CERT_PEMS = (HERE / "demo2_ca.crt.pem",)


def test_sign_pkcs12(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.add_page()
    pdf.sign_pkcs12(HERE / "certs.p12", password=b"1234")
    assert_pdf_equal(pdf, HERE / "sign_pkcs12.pdf", tmp_path)
    check_signature(pdf, TRUSTED_CERT_PEMS)


def test_sign_pkcs12_with_link(tmp_path):
    "This test ensures that Signature & Link annotations can be combined"
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_font("Helvetica", size=30)
    pdf.add_page()
    pdf.set_xy(80, 50)
    pdf.cell(
        w=50,
        h=20,
        txt="URL link",
        border=1,
        align="C",
        link="https://github.com/PyFPDF/fpdf2",
    )
    pdf.sign_pkcs12(HERE / "certs.p12", password=b"1234")
    assert_pdf_equal(pdf, HERE / "sign_pkcs12_with_link.pdf", tmp_path)
    check_signature(pdf, TRUSTED_CERT_PEMS)
