from datetime import timezone
from pathlib import Path
from unittest.mock import patch


from fpdf import FPDF
from test.conftest import assert_pdf_equal, check_signature, EPOCH


HERE = Path(__file__).resolve().parent
TRUSTED_CERT_PEMS = (HERE / "demo2_ca.crt.pem",)


class mock_datetime:
    @staticmethod
    def now(tz):
        return EPOCH.replace(tzinfo=timezone.utc)


# This monkey-patching is needed (at the time of endesive v2.0.9)
# to ensure the signature is always the same,
# due to endesive.signer.sign() depending on datetime.now():
@patch("endesive.signer.datetime", mock_datetime)
def test_sign_pkcs12(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.add_page()
    pdf.sign_pkcs12(HERE / "certs.p12", password=b"1234")
    assert_pdf_equal(pdf, HERE / "sign_pkcs12.pdf", tmp_path)
    check_signature(pdf, TRUSTED_CERT_PEMS)
