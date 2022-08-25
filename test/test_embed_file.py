from pathlib import Path

from fpdf import FPDF

from test.conftest import assert_pdf_equal, EPOCH
import pytest

HERE = Path(__file__).resolve().parent
EMBEDDED_FILE = HERE / "requirements.txt"


def test_embed_file_self(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(EMBEDDED_FILE, modification_date=False)
    assert_pdf_equal(pdf, HERE / "embed_file_self.pdf", tmp_path)


def test_embed_file_all_optionals(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(
        str(EMBEDDED_FILE),
        desc="Source Python code",
        creation_date=EPOCH,
        modification_date=EPOCH,
        compress=True,
        checksum=True,
    )
    assert_pdf_equal(pdf, HERE / "embed_file_all_optionals.pdf", tmp_path)


def test_embed_file_from_bytes(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(bytes=b"Hello world!", basename="hello_world.txt")
    assert_pdf_equal(pdf, HERE / "embed_file_from_bytes.pdf", tmp_path)


def test_embed_file_invalid_params():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        pdf.embed_file(__file__, bytes=b"...")
    with pytest.raises(ValueError):
        pdf.embed_file(__file__, basename=b"file.txt")
    with pytest.raises(ValueError):
        pdf.embed_file(bytes=b"...")
    with pytest.raises(ValueError):
        pdf.embed_file(basename=b"file.txt")


def test_embed_file_duplicate():
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(EMBEDDED_FILE)
    with pytest.raises(ValueError):
        pdf.embed_file(EMBEDDED_FILE)
