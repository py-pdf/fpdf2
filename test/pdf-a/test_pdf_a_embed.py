import logging
from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.enums import DocumentCompliance
from fpdf.errors import PDFAComplianceError
from test.conftest import EPOCH, assert_pdf_equal

HERE = Path(__file__).resolve().parent
DUMMY_TXT_FILE = b"fpdf2"


def minimal_pdf(compliance) -> bytearray:
    mpdf = FPDF(enforce_compliance=compliance)
    mpdf.creation_date = EPOCH
    mpdf.add_page()
    return mpdf.output()


@pytest.mark.parametrize("dc", [DocumentCompliance.PDFA_1B])
def test_pdfa1_forbids_embed(dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    with pytest.raises(PDFAComplianceError) as err:
        pdf.embed_file(bytes=DUMMY_TXT_FILE, basename="test.txt")
    assert (
        str(err.value)
        == f"Embedding files is not allowed for documents compliant with {dc.label}"
    )


@pytest.mark.parametrize(
    "dc",
    [DocumentCompliance.PDFA_2B, DocumentCompliance.PDFA_2U, DocumentCompliance.PDFA_4],
)
def test_pdfa_2_and_4_allows_only_pdf_and_warns(tmp_path, caplog, dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    with caplog.at_level(logging.WARNING):
        pdf.embed_file(
            bytes=minimal_pdf(dc),
            basename="a.pdf",
            modification_date=EPOCH,
            mime_type="application/pdf",
        )
    # Warn that the embedded PDF must itself be PDF/A:
    assert any(
        f"{dc.label}: ensure the embedded PDF 'a.pdf' is itself PDF/A to remain compliant."
        in r.getMessage()
        for r in caplog.records
    )
    assert_pdf_equal(pdf, HERE / f"{dc.name.lower()}_embed_pdf.pdf", tmp_path)


@pytest.mark.parametrize(
    "dc",
    [DocumentCompliance.PDFA_2B, DocumentCompliance.PDFA_2U, DocumentCompliance.PDFA_4],
)
def test_pdfa_2_and_4_base_forbids_embed_other(dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    with pytest.raises(PDFAComplianceError) as err:
        pdf.embed_file(
            bytes=b"col1,col2\n1,2\n",
            basename="data.csv",
            modification_date=EPOCH,
            mime_type="text/csv",
            associated_file_relationship="Data",
        )
    assert (
        str(err.value)
        == f"{dc.label} permits embedding only PDF files, which must themselves be PDF/A."
    )


@pytest.mark.parametrize(
    "dc",
    [DocumentCompliance.PDFA_2B, DocumentCompliance.PDFA_2U, DocumentCompliance.PDFA_4],
)
def test_pdfa_2_non_pdf_rejected(dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    with pytest.raises(PDFAComplianceError) as err:
        pdf.embed_file(bytes=DUMMY_TXT_FILE, basename="test.txt")
    assert (
        str(err.value)
        == f"{dc.label} permits embedding only PDF files, which must themselves be PDF/A."
    )


@pytest.mark.parametrize("dc", [DocumentCompliance.PDFA_3B, DocumentCompliance.PDFA_3U])
def test_pdfa_3_embeds_txt_with_filespec_and_subtype(tmp_path, dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    pdf.embed_file(
        bytes=DUMMY_TXT_FILE,
        basename="test.txt",
        modification_date=EPOCH,
        mime_type="text/plain",
        associated_file_relationship="Data",
    )
    assert_pdf_equal(pdf, HERE / f"{str(dc).lower()}_embed_txt.pdf", tmp_path)


@pytest.mark.parametrize("dc", [DocumentCompliance.PDFA_4F, DocumentCompliance.PDFA_4E])
def test_pdfa_4_variants_embed_with_af(tmp_path, dc):
    pdf = FPDF(enforce_compliance=dc)
    pdf.add_page()
    pdf.embed_file(
        bytes=b"col1,col2\n1,2\n",
        basename="data.csv",
        modification_date=EPOCH,
        mime_type="text/csv",
        associated_file_relationship="Data",
    )
    assert_pdf_equal(pdf, HERE / f"{str(dc).lower()}_embed_csv.pdf", tmp_path)


def test_pdfa_4f_requires_embedded_file():
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_4F)
    pdf.add_page()
    with pytest.raises(PDFAComplianceError) as err:
        pdf.output()
    assert str(err.value) == "PDF/A-4F requires at least one embedded file"
