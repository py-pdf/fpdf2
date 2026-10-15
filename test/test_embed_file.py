import sys
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from fpdf import FPDF
from fpdf.enums import FileAttachmentAppearance
from test.conftest import assert_pdf_equal, EPOCH

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize("compress", [False, True])
@pytest.mark.parametrize(
    "contents, digest",
    [
        (b"hello", "5d41402abc4b2a76b9719d911017c592"),
        (b"Hello world", "3e25960a79dbc69b674cd4ec67a72c62"),
    ],
)
def test_embed_file_checksum_of_uncompressed_data(compress, contents, digest):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(
        bytes=contents, basename="payload.txt", compress=compress, checksum=True
    )
    reader = PdfReader(BytesIO(pdf.output()))
    attachment = reader.trailer["/Root"]["/Names"]["/EmbeddedFiles"]["/Names"][1]
    stream = attachment["/EF"]["/F"]
    assert stream.get_data() == contents
    assert stream["/Params"]["/CheckSum"].original_bytes == bytes.fromhex(digest)


def _make_text_file(tmp_path: Path) -> Path:
    return _make_text_file_with_name(tmp_path, "helloworld.txt")


def _make_text_file_with_name(tmp_path: Path, filename: str) -> Path:
    p = tmp_path / filename
    p.write_text("Hello world", encoding="utf-8")
    return p


def test_embed_file_self(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(_make_text_file(tmp_path), modification_date=False)
    assert_pdf_equal(pdf, HERE / "embed_file_self.pdf", tmp_path)


def test_embed_file_parens(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(
        _make_text_file_with_name(tmp_path, "helloworld(1).txt"),
        modification_date=False,
    )
    assert_pdf_equal(pdf, HERE / "embed_file_parens.pdf", tmp_path)


def test_embed_file_single_parens(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(
        _make_text_file_with_name(tmp_path, "helloworld(1.txt"),
        modification_date=False,
        desc="with (parens",
    )
    assert_pdf_equal(pdf, HERE / "embed_file_single_parens.pdf", tmp_path)


@pytest.mark.skipif(
    sys.platform in ("cygwin", "win32") and sys.version_info[:2] >= (3, 14),
    reason="Skipped on Windows with Python 3.14+ due to zlib compressed data differences",
)
def test_embed_file_all_optionals(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(
        str(_make_text_file(tmp_path)),
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


@pytest.mark.parametrize("compress", [False, True])
@pytest.mark.parametrize("source", ["bytes", "path"])
def test_embed_empty_file(tmp_path, compress, source):
    pdf = FPDF()
    pdf.add_page()
    if source == "bytes":
        pdf.embed_file(bytes=b"", basename="empty.txt", compress=compress)
    else:
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        pdf.embed_file(empty_file, compress=compress)
    reader = PdfReader(BytesIO(pdf.output()))
    assert list(reader.attachments["empty.txt"]) == [b""]
    names = reader.trailer["/Root"]["/Names"]["/EmbeddedFiles"]["/Names"]
    stream = names[1].get_object()["/EF"]["/F"].get_object()
    assert stream["/Params"]["/Size"] == 0


def test_embed_file_rejects_empty_bytes_with_file_path(tmp_path):
    pdf = FPDF()
    with pytest.raises(ValueError, match="'bytes' cannot be provided with 'file_path'"):
        pdf.embed_file(_make_text_file(tmp_path), bytes=b"")


def test_file_attachment_annotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.file_attachment_annotation(
        _make_text_file(tmp_path), modification_date=False, x=50, y=50
    )
    assert_pdf_equal(pdf, HERE / "file_attachment_annotation.pdf", tmp_path)


def test_file_attachment_annotation_hide_icon(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    annotation = pdf.file_attachment_annotation(
        _make_text_file(tmp_path),
        modification_date=False,
        x=50,
        y=50,
        appearance=FileAttachmentAppearance.HIDDEN,
    )
    # The file stays embedded and reachable through the annotation's /FS entry,
    # only its default icon is hidden through an empty appearance stream:
    assert annotation.f_s is not None
    assert_pdf_equal(pdf, HERE / "file_attachment_annotation_hide_icon.pdf", tmp_path)


def test_embed_file_invalid_params():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        pdf.embed_file(__file__, bytes=b"...")
    with pytest.raises(ValueError):
        pdf.embed_file(__file__, basename="file.txt")
    with pytest.raises(ValueError):
        pdf.embed_file(bytes=b"...")
    with pytest.raises(ValueError):
        pdf.embed_file(basename="file.txt")


def test_embed_file_duplicate(tmp_path):
    EMBEDDED_FILE = _make_text_file(tmp_path)
    pdf = FPDF()
    pdf.add_page()
    pdf.embed_file(EMBEDDED_FILE)
    with pytest.raises(ValueError):
        pdf.embed_file(EMBEDDED_FILE)
