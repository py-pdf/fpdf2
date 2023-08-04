# pylint: disable=protected-access
from os import devnull
from pathlib import Path
import sys

import pytest

from fpdf import FPDF
from fpdf.encryption import StandardSecurityHandler as sh
from fpdf.enums import AccessPermission, EncryptionMethod
from fpdf.errors import FPDFException
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
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Producer="py-pdf/fpdf2.X.Y"/>
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
    pdf._security_handler.get_random_bytes = fixed_iv
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


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="fontTools dropped support for 3.7. https://github.com/py-pdf/fpdf2/pull/863",
)
def test_encrypt_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(
        "Quicksand", style="", fname=HERE.parent / "fonts" / "Quicksand-Regular.otf"
    )
    pdf.add_font(
        "Quicksand", style="B", fname=HERE.parent / "fonts" / "Quicksand-Bold.otf"
    )
    pdf.add_font(
        "Quicksand", style="I", fname=HERE.parent / "fonts" / "Quicksand-Italic.otf"
    )
    pdf.set_font("Quicksand", size=32)
    text = (
        # pylint: disable=implicit-str-concat
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(w=pdf.epw, txt=text, markdown=True)
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, txt=text, markdown=True, align="L")
    pdf.set_encryption(owner_password="fpdf2")
    assert_pdf_equal(pdf, HERE / "encrypt_fonts.pdf", tmp_path)


def test_encryption_with_hyperlink(tmp_path):  # issue 672
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica")
    pdf.cell(txt="hyperlink", link="https://github.com/py-pdf/fpdf2")
    pdf.set_encryption(owner_password="fpdf2")
    assert_pdf_equal(pdf, HERE / "encryption_with_hyperlink.pdf", tmp_path)


def test_encrypt_outline(tmp_path):  # issue 732
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica")
    pdf.start_section("Title")
    pdf.start_section("Subtitle", level=1)
    pdf.set_encryption(owner_password="fpdf2")
    assert_pdf_equal(pdf, HERE / "encrypt_outline.pdf", tmp_path)


def test_encryption_aes256(tmp_path):
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
    pdf.text(50, 50, "Some text")
    pdf.ink_annotation(
        [(40, 50), (70, 25), (100, 50), (70, 75), (40, 50)],
        title="Lucas",
        contents="Some encrypted annotation",
    )
    pdf.set_encryption(
        owner_password="fpdf2",
        encryption_method=EncryptionMethod.AES_256,
        permissions=AccessPermission.none(),
    )
    pdf._security_handler.get_random_bytes = fixed_iv
    assert_pdf_equal(pdf, HERE / "encryption_aes256.pdf", tmp_path)


def test_encryption_aes256_with_user_password(tmp_path):
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
        user_password="1" * 1000,
        encryption_method=EncryptionMethod.AES_256,
        permissions=AccessPermission.all(),
    )
    pdf._security_handler.get_random_bytes = fixed_iv
    assert_pdf_equal(pdf, HERE / "encryption_aes256_user_password.pdf", tmp_path)


def test_blank_owner_password():
    pdf = FPDF()
    pdf.set_encryption(
        owner_password="",
        encryption_method=EncryptionMethod.AES_256,
        permissions=AccessPermission.none(),
    )
    with pytest.raises(FPDFException) as e:
        pdf.output(devnull)
    assert str(e.value) == "Invalid owner password "


def test_password_prep():
    """
    The PDF standard requires the passwords to be prepared using the stringprep algorithm
    using the SASLprep as per RFC 4013
    https://datatracker.ietf.org/doc/html/rfc4013
    Those assertions are bases on the examples section of the RFC
    """
    assert sh.prepare_string("I\xadX") == b"IX"  # SOFT HYPHEN mapped to nothing
    assert sh.prepare_string("user") == b"user"  # no transformation
    assert sh.prepare_string("USER") == b"USER"  # case preserved
    assert sh.prepare_string("\xaa") == b"a"  # output is NFKC, input in ISO 8859-1
    assert sh.prepare_string("\u2168") == b"IX"  # output is NFKC, will match #1
    with pytest.raises(FPDFException) as e:
        sh.prepare_string("\x07")  # Error - prohibited character
    assert str(e.value) == "The password  contains prohibited characters"
    with pytest.raises(FPDFException) as e:
        sh.prepare_string("\u0627\x31")  # Error - bidirectional check
    assert sh.prepare_string("A" * 300) == b"A" * 127  # test cap 127 chars
