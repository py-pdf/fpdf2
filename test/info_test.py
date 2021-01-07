"""put_info_test.py"""

import unittest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(".."))
)

import fpdf
import test
from test.utilities import relative_path_to, calculate_hash_of_file, set_doc_date_0


def document_operations(doc):
    set_doc_date_0(doc)
    doc.add_page()
    doc.set_font("Arial", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=0, link="")


class CatalogDisplayModeTest(unittest.TestCase):
    """This test tests some possible inputs to FPDF#_put_info."""

    def test_put_info_all(self):
        doc = fpdf.FPDF()
        document_operations(doc)
        doc.set_title("sample title")
        doc.set_subject("sample subject")
        doc.set_author("sample author")
        doc.set_keywords("sample keywords")
        doc.set_creator("sample creator")
        # doc.set_creation_date()

        output = relative_path_to("put_info_test.pdf")
        doc.output(output)
        # print(calculate_hash_of_file(output))
        known_good_hash = "64d87472bd5e369441dac2b092a249d8"
        self.assertEqual(calculate_hash_of_file(output), known_good_hash)
        os.unlink(output)

    def test_put_info_some(self):
        doc = fpdf.FPDF()
        document_operations(doc)
        doc.set_title("sample title")
        # doc.set_subject('sample subject')
        # doc.set_author('sample author')
        doc.set_keywords("sample keywords")
        doc.set_creator("sample creator")
        # doc.set_creation_date()

        output = relative_path_to("put_info_test.pdf")
        doc.output(output)
        # print(calculate_hash_of_file(output))
        known_good_hash = "bcc272f353be1acb76c5caf3f662b9af"
        self.assertEqual(calculate_hash_of_file(output), known_good_hash)
        os.unlink(output)


if __name__ == "__main__":
    unittest.main()

## test was written in place
