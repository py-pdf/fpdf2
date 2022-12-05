from pathlib import Path

from fpdf import FPDF
from fpdf.enums import AccessPermission, EncryptionMethod
from test.conftest import assert_pdf_equal, EPOCH

HERE = Path(__file__).resolve().parent


def test_encryption_rc4(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(owner_password="fpdf2", permissions=AccessPermission.all())
    assert_pdf_equal(pdf, HERE / "encryption_rc4.pdf", tmp_path)


def test_encryption_rc4_permissions(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(
        owner_password="fpdf2",
        permissions=AccessPermission.PRINT_LOW_RES | AccessPermission.PRINT_HIGH_RES,
    )
    assert_pdf_equal(pdf, HERE / "encryption_rc4_permissions.pdf", tmp_path)


def test_no_encryption(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(
        owner_password="fpdf2",
        encryption_method=EncryptionMethod.NO_ENCRYPTION,
        permissions=AccessPermission.none(),
    )
    assert_pdf_equal(pdf, HERE / "no_encryption.pdf", tmp_path)


def test_encryption_rc4_user_password(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(
        owner_password="fpdf2",
        user_password="654321",
        permissions=AccessPermission.PRINT_LOW_RES | AccessPermission.PRINT_HIGH_RES,
    )
    assert_pdf_equal(pdf, HERE / "encryption_rc4_user_password.pdf", tmp_path)


def test_encryption_aes128(tmp_path):
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)

    def fixed_iv(size):
        return bytearray(size)

    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(
        owner_password="fpdf2",
        encryption_method=EncryptionMethod.AES_128,
        permissions=AccessPermission.none(),
    )
    pdf._security_handler.get_initialization_vector = fixed_iv
    assert_pdf_equal(pdf, HERE / "encryption_aes128.pdf", tmp_path)
