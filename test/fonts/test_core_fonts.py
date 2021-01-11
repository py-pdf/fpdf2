from fpdf import FPDF
from fpdf.errors import FPDFException
import unittest
from test.utilities import assert_pdf_equal

# python -m unittest test.fonts.test_core_fonts


class CoreFontsTest(unittest.TestCase):
    def test_no_set_font(self):
        pdf = FPDF()
        pdf.add_page()
        with self.assertRaises(FPDFException) as e:
            pdf.text(10, 10, "Hello World!")
        self.assertEqual(
            str(e.exception), "No font set, you need to call set_font() beforehand"
        )

    def test_set_core_font(self):
        pdf = FPDF()
        pdf.add_page()
        for i, font_name in enumerate(pdf.core_fonts.keys()):
            pdf.set_font(font_name, "", 36)
            pdf.text(10, 10 + 10 * i, "Hello World!")
        assert_pdf_equal(self, pdf, "test_set_core_font.pdf")


if __name__ == "__main__":
    unittest.main()
