# pylint: disable=protected-access
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import AccessPermission, EncryptionMethod
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

XMP_METADATA = """<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="fpdf2">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="">
      <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">My document title</rdf:li>
        </rdf:Alt>
      </dc:title>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">This is a test document for fpdf2 with XMP metadata</rdf:li>
        </rdf:Alt>
      </dc:description>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Seq>
          <rdf:li>Lucas Cimon</rdf:li>
        </rdf:Seq>
      </dc:creator>
    </rdf:Description>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Keywords="test data pdf fpdf2"/>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Producer="PyFPDF/fpdf2.X.Y"/>
    <rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" rdf:about="" xmp:CreatorTool="fpdf2"/>
  </rdf:RDF>
</x:xmpmeta>"""


def test_encryption_rc4(tmp_path):
    pdf = FPDF()
    pdf.set_author("author")
    pdf.set_subject("string to be encrypted")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(owner_password="fpdf2", permissions=AccessPermission.all())
    assert_pdf_equal(pdf, HERE / "encryption_rc4.pdf", tmp_path)


def test_encryption_rc4_permissions(tmp_path):
    pdf = FPDF()
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

    def custom_file_id():
        return pdf._default_file_id(bytearray([0xFF]))

    pdf.file_id = custom_file_id
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


def test_encryption_empty_user_password(tmp_path):
    pdf = FPDF()
    pdf.set_encryption(owner_password="fpdf2", user_password="")
    assert_pdf_equal(pdf, HERE / "encryption_empty_user_password.pdf", tmp_path)


def test_encryption_rc4_user_password(tmp_path):
    pdf = FPDF()

    def custom_file_id():
        return pdf._default_file_id(bytearray([0xFF]))

    pdf.file_id = custom_file_id
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

    def custom_file_id():
        return pdf._default_file_id(bytearray([0xFF]))

    pdf.file_id = custom_file_id

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


def test_encrypt_metadata(tmp_path):
    pdf = FPDF()

    def custom_file_id():
        # return pdf._default_file_id(bytearray([0xFF]))
        return "<AC2718D5DA802D34E7F97EEF0A0B52C5><AC2718D5DA802D34E7F97EEF0A0B52C5>"

    pdf.file_id = custom_file_id
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(txt="hello world")
    pdf.set_encryption(
        owner_password="fpdf2",
        encrypt_metadata=True,
    )
    pdf.set_xmp_metadata(XMP_METADATA)
    assert_pdf_equal(pdf, HERE / "encrypt_metadata.pdf", tmp_path)
