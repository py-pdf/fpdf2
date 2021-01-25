from datetime import datetime
from pathlib import Path

import pytest

import fpdf
from fpdf.errors import FPDFException
from test.utilities import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_setting_bad_date():
    doc = fpdf.FPDF()
    doc.set_creation_date("i am not a date")
    with pytest.raises(FPDFException):
        doc.output("output.pdf")


def test_setting_old_date(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    # 2017, April 18th, almost 7:09a
    date = datetime(2017, 4, 18, 7, 8, 55)
    doc.set_creation_date(date)
    assert_pdf_equal(doc, HERE / "setting_old_date.pdf", tmp_path)
