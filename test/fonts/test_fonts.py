from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.errors import FPDFException
from test.utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_no_set_font():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as e:
        pdf.text(10, 10, "Hello World!")
    expected_msg = "No font set, you need to call set_font() beforehand"
    assert str(e.value) == expected_msg


def test_set_unknown_font():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(FPDFException) as e:
        pdf.set_font("Dummy")
    assert (
        str(e.value)
        == "Undefined font: dummy - Use built-in fonts or FPDF.add_font() beforehand"
    )


def test_set_builtin_font(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    builtin_fonts = sorted(
        f for f in pdf.core_fonts if not any(f.endswith(s) for s in ("B", "I", "BI"))
    )
    for i, font_name in enumerate(builtin_fonts):
        styles = (
            ("",) if font_name in ("symbol", "zapfdingbats") else ("", "B", "I", "BI")
        )
        for j, style in enumerate(styles):
            pdf.set_font(font_name.capitalize(), style, 36)
            pdf.set_font(font_name.lower(), style, 36)
            pdf.text(0, 10 + 40 * i + 10 * j, "Hello World!")
    assert_pdf_equal(pdf, HERE / "fonts_set_builtin_font.pdf", tmp_path)


def test_issue_66(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", "B", 14)
    pdf.cell(50, 0, "ABC")
    pdf.set_font("Times", size=10)
    pdf.cell(50, 0, "DEF")
    # Setting the font to an already used one used to remove the text!
    pdf.set_font("Times", "B", 14)
    assert_pdf_equal(pdf, HERE / "fonts_issue_66.pdf", tmp_path)
