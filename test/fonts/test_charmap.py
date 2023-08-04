"""Charmap Test Case

This module contains the test case for the Charmap Test. It prints the first
999 characters of the unicode character set with a unicode ttf font, and
verifies the result against a known good result.

This test will complain that some of the values in this font file are out of
the range of the C 'short' data type (2 bytes, 0 - 65535):
  fpdf/ttfonts.py:671: UserWarning: cmap value too big/small:
and this seems to be okay.
"""
import logging
from pathlib import Path
import sys

from fontTools.ttLib import TTFont
import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal, ensure_exec_time_below

HERE = Path(__file__).resolve().parent


@pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="fontTools dropped support for 3.7. https://github.com/py-pdf/fpdf2/pull/863",
)
@pytest.mark.parametrize(
    "font_filename",
    [
        font_file.name
        for font_file in HERE.glob("*.*tf")
        if not any(
            exclude in font_file.stem
            for exclude in ("Bold", "Italic", "NotoColorEmoji")
        )
    ],
)
@ensure_exec_time_below(seconds=10)  # TwitterEmoji.ttf is the longest to process
def test_charmap_first_999_chars(caplog, font_filename, tmp_path):
    """
    Character Map Test
    from PyFPDF version 1.7.2: github.com/reingart/pyfpdf/commit/2eab310cfd866ce24947c3a9d850ebda7c6d515d
    """
    caplog.set_level(logging.ERROR)  # hides fonttool warnings

    font_path = HERE / font_filename
    font_name = font_path.stem

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(fname=font_path)
    pdf.set_font(font_name, size=10)

    font = TTFont(font_path, lazy=True)
    cmap = font.getBestCmap()

    # Create a PDF with the first 999 characters defined in the font:
    for counter, character in enumerate(list(cmap.keys())[:1000]):
        pdf.write(8, f"{counter:03}) {character:03x} - {character:c}", print_sh=True)
        pdf.ln()

    assert_pdf_equal(pdf, HERE / f"charmap_first_999_chars-{font_name}.pdf", tmp_path)
