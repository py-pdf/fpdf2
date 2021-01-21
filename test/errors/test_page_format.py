import unittest

import fpdf

# python -m unittest test.errors.page_format.PageFormatErrors
# python -m unittest test.errors.page_format.PageFormatErrorClass


class PageFormatErrorClassTest(unittest.TestCase):
    def test_constructor(self):
        with self.assertRaises(TypeError) as e:
            fpdf.errors.FPDFPageFormatException(None, unknown=True, one=True)

        expected = "FPDF Page Format Exception cannot be both"
        contains = expected in str(e.exception)
        self.assertTrue(contains)


class PageFormatErrorsTest(unittest.TestCase):
    def test_error(self):
        with self.assertRaises(fpdf.errors.FPDFPageFormatException) as e:
            fpdf.fpdf.get_page_format("letter1")

        self.assertTrue("FPDFPageFormatException" in str(e.exception))
        self.assertTrue("Unknown page format" in str(e.exception))
        self.assertTrue("letter1" in str(e.exception))

        with self.assertRaises(fpdf.errors.FPDFPageFormatException) as e:
            fpdf.fpdf.get_page_format(3)

        self.assertTrue("FPDFPageFormatException" in str(e.exception))
        self.assertTrue("Only one argument given" in str(e.exception))

        with self.assertRaises(fpdf.errors.FPDFPageFormatException) as e:
            fpdf.fpdf.get_page_format(4, "a")

        self.assertTrue("FPDFPageFormatException" in str(e.exception))
        self.assertTrue("Arguments must be numbers: " in str(e.exception))
