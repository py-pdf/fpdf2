from pathlib import Path

from fpdf import FPDF, XPos, YPos
from fpdf.substitution import SubstitutionAlign
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_substitution_simplest_case(tmp_path):
    """
    We put only a substitution with the mask "hello" in the file.
    Then we assign the word "world" to the substitution.

    Expected behavior:
        The file contains only the word "world".
    """
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    substitution = pdf.create_substitution("hello")
    pdf.cell(text=str(substitution))

    substitution.value = "world"
    assert_pdf_equal(pdf, HERE / "substitution_simplest_case.pdf", tmp_path)


def test_substitution_alignment(tmp_path):
    """
    We have two cases: the mask is longer than the value and the value is longer than the mask.
    For both cases, we test different alignment options.

    Expected behavior:
        Alignment works as expected.
        If the value is longer, there will be empty space.
        If the mask is longer, the value will overlap the leading or following text, if any.
    """
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for mask, value, align in (
        # mask > value, left align
        ("long long mask", "value", SubstitutionAlign.L),
        # mask > value, center
        (
            "long long mask",
            "value",
            SubstitutionAlign.C,
        ),
        # mask > value, right align
        (
            "long long mask",
            "value",
            SubstitutionAlign.R,
        ),
        ("mask", "long value", SubstitutionAlign.L),  # mask < value, left align
        ("mask", "long value", SubstitutionAlign.C),  # mask < value, center
        ("mask", "long value", SubstitutionAlign.R),  # mask < value, right align
    ):
        sub = pdf.create_substitution(mask, align=align)
        sub.value = value
        pdf.cell(text=f"Lorem {sub} ipsum", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    assert_pdf_equal(pdf, HERE / "substitution_alignment.pdf", tmp_path)
