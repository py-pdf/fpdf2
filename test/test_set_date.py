from datetime import datetime

import pytest

import fpdf
from test.utilities import assert_pdf_equal


class TestCreationDate:
    def test_setting_bad_date(self):
        doc = fpdf.FPDF()
        doc.set_creation_date("i am not a date")
        with pytest.raises(BaseException):
            doc.output("output.pdf")

    def test_setting_old_date(self):
        doc = fpdf.FPDF()
        doc.add_page()
        # 2017, April 18th, almost 7:09a
        date = datetime(2017, 4, 18, 7, 8, 55)
        doc.set_creation_date(date)
        assert_pdf_equal(self, doc, "setting_old_date.pdf")
