from fpdf import FPDF
import unittest
from test.utilities import assert_pdf_equal

# python -m unittest test.test_code39


class Code39Test(unittest.TestCase):
    def test_code39(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.code39("fpdf2", x=50, y=50, w=4, h=20)
        pdf.set_font("courier", "B", size=36)
        pdf.text(x=80, y=80, txt="fpdf2")
        assert_pdf_equal(self, pdf, "test_code39.pdf")


if __name__ == "__main__":
    unittest.main()
