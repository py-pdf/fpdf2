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

    def test_set_builtin_font(self):
        pdf = FPDF()
        pdf.add_page()
        builtin_fonts = sorted(
            f
            for f in pdf.core_fonts
            if not any(f.endswith(s) for s in ("B", "I", "BI"))
        )
        for i, font_name in enumerate(builtin_fonts):
            styles = (
                ("",)
                if font_name in ("symbol", "zapfdingbats")
                else ("", "B", "I", "BI")
            )
            for j, style in enumerate(styles):
                pdf.set_font(font_name.capitalize(), style, 36)
                pdf.set_font(font_name.lower(), style, 36)
                pdf.text(0, 10 + 40 * i + 10 * j, "Hello World!")
        assert_pdf_equal(self, pdf, "test_set_builtin_font.pdf", generate=True)


if __name__ == "__main__":
    unittest.main()
