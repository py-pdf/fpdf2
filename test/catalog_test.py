import unittest

import fpdf
from test.utilities import assert_pdf_equal

# python -m unittest test.catalog_test


def document_operations(doc):
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=0, link="")


class CatalogDisplayModeTest(unittest.TestCase):
    """This test executes some possible inputs to FPDF#set_display_mode."""

    def test_setting_all_zoom(self):
        for zoom_input in ["fullpage", "fullwidth", "real", "default"]:
            with self.subTest(zoom_input=zoom_input):
                doc = fpdf.FPDF()
                document_operations(doc)
                doc.set_display_mode(zoom=zoom_input, layout="continuous")
                assert_pdf_equal(self, doc, "catalog-zoom-" + zoom_input + ".pdf")

    def test_setting_all_layout(self):
        for layout_input in ["single", "continuous", "two", "default"]:
            with self.subTest(layout_input=layout_input):
                doc = fpdf.FPDF()
                document_operations(doc)
                doc.set_display_mode(zoom="default", layout=layout_input)
                assert_pdf_equal(self, doc, "catalog-layout-" + layout_input + ".pdf")


if __name__ == "__main__":
    unittest.main()
