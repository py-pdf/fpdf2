from datetime import datetime, timezone
from pathlib import Path

import pytest

import fpdf
from fpdf.errors import FPDFException
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_setting_bad_date():
    doc = fpdf.FPDF()
    with pytest.raises(TypeError):
        doc.set_creation_date("i am not a date")


def test_setting_old_date(tmp_path):
    doc = fpdf.FPDF()
    doc.add_page()
    # 2017, April 18th, almost 7:09a
    doc.set_creation_date(datetime(2017, 4, 18, 7, 8, 55).replace(tzinfo=timezone.utc))
    assert_pdf_equal(doc, HERE / "setting_old_date.pdf", tmp_path, at_epoch=False)
