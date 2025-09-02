from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.enums import DocumentCompliance
from fpdf.errors import PDFAComplianceError

HERE = Path(__file__).resolve().parent


def test_pdfa_2b_encryption():
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_2B)
    with pytest.raises(PDFAComplianceError) as error:
        pdf.set_encryption(owner_password="fpdf2")
    assert (
        str(error.value)
        == "Encryption is now allowed for documents compliant with PDF/A-2B"
    )


def test_pdfa_3b_encryption():
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_3B)
    with pytest.raises(PDFAComplianceError) as error:
        pdf.set_encryption(owner_password="fpdf2")
    assert (
        str(error.value)
        == "Encryption is now allowed for documents compliant with PDF/A-3B"
    )


def test_pdfa_2b_core_font():
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_2B)
    with pytest.raises(PDFAComplianceError) as error:
        pdf.set_font("helvetica", "", 12)
    assert (
        str(error.value)
        == "Usage of base fonts is now allowed for documents compliant with PDF/A-2B. Use add_font() to embed a font file"
    )


def test_pdfa_3b_core_font():
    pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_3B)
    with pytest.raises(PDFAComplianceError) as error:
        pdf.set_font("helvetica", "", 12)
    assert (
        str(error.value)
        == "Usage of base fonts is now allowed for documents compliant with PDF/A-3B. Use add_font() to embed a font file"
    )
