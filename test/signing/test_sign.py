from pathlib import Path
from sys import version_info


from pytest import mark
from fpdf import FPDF
from test.conftest import assert_pdf_equal, check_signature, EPOCH


HERE = Path(__file__).resolve().parent
TRUSTED_CERT_PEMS = (HERE / "signing-certificate.crt",)


def test_endesive_debug():
    import endesive

    print("Endesive modules:", dir(endesive))
    try:
        from endesive import signer

        print("endesive.signer imported successfully.")
    except ImportError as e:
        print("Failed to import endesive.signer:", e)
        assert False, "endesive.signer failed to import"


@mark.skipif(version_info[:2] == (3, 8), reason="Endesive doesn't support Python 3.8")
def test_sign_pkcs12(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.add_page()
    pdf.sign_pkcs12(HERE / "signing-certificate.p12", password=b"fpdf2")
    assert_pdf_equal(pdf, HERE / "sign_pkcs12.pdf", tmp_path)
    check_signature(pdf, TRUSTED_CERT_PEMS)


@mark.skipif(version_info[:2] == (3, 8), reason="Endesive doesn't support Python 3.8")
def test_sign_pkcs12_with_link(tmp_path):
    "This test ensures that Signature & Link annotations can be combined"
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_font("Helvetica", size=30)
    pdf.add_page()
    pdf.text(x=80, y=50, text="Page 1/2")
    pdf.add_page()
    pdf.set_xy(80, 50)
    pdf.sign_pkcs12(HERE / "signing-certificate.p12", password=b"fpdf2")
    pdf.cell(
        w=50,
        h=20,
        text="URL link",
        border=1,
        align="C",
        link="https://github.com/py-pdf/fpdf2",
    )
    assert_pdf_equal(pdf, HERE / "sign_pkcs12_with_link.pdf", tmp_path)
    check_signature(pdf, TRUSTED_CERT_PEMS)
