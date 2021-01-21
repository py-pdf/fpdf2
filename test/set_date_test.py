import unittest

import fpdf
from test.utilities import assert_pdf_equal

from datetime import datetime


class CreationDateTest(unittest.TestCase):
    def test_setting_bad_date(self):
        doc = fpdf.FPDF()
        doc.set_creation_date("i am not a date")
        with self.assertRaises(BaseException):
            doc.output("output.pdf")

    def test_setting_old_date(self):
        doc = fpdf.FPDF()
        doc.add_page()
        # 2017, April 18th, almost 7:09a
        date = datetime(2017, 4, 18, 7, 8, 55)
        doc.set_creation_date(date)
        assert_pdf_equal(self, doc, "setting_old_date.pdf")


if __name__ == "__main__":
    unittest.main()
