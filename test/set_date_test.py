"""metadata_test.py"""

import unittest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(".."))
)

import fpdf
import test
from test.utilities import relative_path_to, calculate_hash_of_file

import datetime

# doc = fpdf.FPDF()
# doc.add_page()
# # 2017, April 18th, almost 7:09a
# date = datetime.datetime(2017, 4, 18, 7, 8, 55)
# doc.set_creation_date(date)

# output = relative_path_to('output.pdf')
# doc.output(output)
# result_hash = calculate_hash_of_file(output)
# assert("b4b210a31bcb3d741508f3d2d005adf9" == result_hash)
# print(result_hash)
# os.unlink(output)


class CreationDateTest(unittest.TestCase):
    def test_setting_bad_date(self):
        doc = fpdf.FPDF()
        doc.set_creation_date("i am not a date")
        output = relative_path_to("output.pdf")
        with self.assertRaises(BaseException):
            doc.output(output)

    def test_setting_old_date(self):
        doc = fpdf.FPDF()
        doc.add_page()
        # 2017, April 18th, almost 7:09a
        date = datetime.datetime(2017, 4, 18, 7, 8, 55)
        doc.set_creation_date(date)

        output = relative_path_to("output.pdf")
        doc.output(output)

        known_good_hash = "b4b210a31bcb3d741508f3d2d005adf9"
        result_hash = calculate_hash_of_file(output)
        self.assertEqual(known_good_hash, result_hash)
        os.unlink(output)

    def test_unequal_dates(self):
        old_doc = fpdf.FPDF()
        old_doc.add_page()
        # 2017, April 18th, almost 7:09a
        date = datetime.datetime(2017, 4, 18, 7, 8, 55)
        old_doc.set_creation_date(date)

        output = relative_path_to("output.pdf")
        old_doc.output(output)

        # known_good_hash = "b4b210a31bcb3d741508f3d2d005adf9"
        old_result_hash = calculate_hash_of_file(output)
        os.unlink(output)

        new_doc = fpdf.FPDF()
        new_doc.add_page()
        new_doc.set_creation_date()  # now
        output = relative_path_to("output.pdf")
        new_doc.output(output)

        new_result_hash = calculate_hash_of_file(output)
        os.unlink(output)

        self.assertNotEqual(old_result_hash, new_result_hash)


if __name__ == "__main__":
    unittest.main()
