import unittest
import sys
import os
import fpdf

# python -m unittest test.errors.FPDF_errors.AddPage
# python -m unittest test.errors.FPDF_errors.Orientation
# python -m unittest test.errors.FPDF_errors.UnitTest
# python -m unittest test.errors.FPDF_errors.DocOption


class AddPageTest(unittest.TestCase):
    def test_throws_without_page(self):
        pdf = fpdf.FPDF()
        with self.assertRaises(Exception) as e:
            pdf.text(1, 2, "ok")

        msg = "No page open, you need to call add_page() first"
        self.assertEqual(str(e.exception), msg)


class OrientationTest(unittest.TestCase):
    def test_portrait_landscape(self):
        l = fpdf.FPDF(orientation="l")
        landscape = fpdf.FPDF(orientation="landscape")
        p = fpdf.FPDF(orientation="p")
        portrait = fpdf.FPDF(orientation="portrait")

        self.assertEqual(l.w_pt, landscape.w_pt)
        self.assertEqual(l.h_pt, landscape.h_pt)
        self.assertEqual(l.def_orientation, landscape.def_orientation)

        self.assertEqual(p.w_pt, portrait.w_pt)
        self.assertEqual(p.h_pt, portrait.h_pt)
        self.assertEqual(p.def_orientation, portrait.def_orientation)

        self.assertEqual(landscape.w_pt, portrait.h_pt)
        self.assertEqual(landscape.h_pt, portrait.w_pt)

    def test_incorrect_orientation(self):
        with self.assertRaises(Exception) as e:
            fpdf.FPDF(orientation="hello")

        msg = "Incorrect orientation: hello"
        self.assertEqual(str(e.exception), msg)


class UnitTest(unittest.TestCase):
    def test_constructor(self):
        with self.assertRaises(Exception) as e:
            fpdf.FPDF(unit="smiles")

        self.assertEqual(str(e.exception), "Incorrect unit: smiles")

        self.assertAlmostEqual(fpdf.FPDF(unit="pt").k, 1)
        self.assertAlmostEqual(fpdf.FPDF(unit="mm").k, 2.83464566929)
        self.assertAlmostEqual(fpdf.FPDF(unit="cm").k, 28.3464566929)
        self.assertAlmostEqual(fpdf.FPDF(unit="in").k, 72)


class DocOptionTest(unittest.TestCase):
    def test_only_core_fonts_encoding(self):
        pdf = fpdf.FPDF()
        pdf.set_doc_option("core_fonts_encoding", 4)
        self.assertEqual(pdf.core_fonts_encoding, 4)

        with self.assertRaises(Exception) as e:
            pdf.set_doc_option("not core_fonts_encoding", None)

        msg = 'Unknown document option "not core_fonts_encoding"'
        self.assertEqual(str(e.exception), msg)
