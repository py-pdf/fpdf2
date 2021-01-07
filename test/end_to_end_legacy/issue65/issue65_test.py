"""issue65_test.py"""

import unittest
import sys
import os

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..", "..")
    ),
)

import fpdf
import test
from test.utilities import relative_path_to, set_doc_date_0, calculate_hash_of_file


@unittest.skip("skip network tests by default")
class Issue65Test(unittest.TestCase):
    def test_issue65(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        png = "https://g.twimg.com/Twitter_logo_blue.png"
        pdf.image(png, x=15, y=15, w=30, h=25)

        set_doc_date_0(pdf)
        test = relative_path_to("issue65_test.pdf")
        pdf.output(test, "F")

        known_good_hash = "ed3d7f6430a8868d3e9587170aa2f678"
        self.assertEqual(known_good_hash, calculate_hash_of_file(test))
        os.unlink(test)

    def test_jpg(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        jpg = (
            "https://upload.wikimedia.org/wikipedia/commons/8/8c/"
            "JPEG_example_JPG_RIP_025.jpg"
        )
        pdf.image(jpg, x=15, y=15)

        set_doc_date_0(pdf)
        test = relative_path_to("issue65_test.pdf")
        pdf.output(test, "F")

        known_good_hash = "0486acfcd75597cc52ca2eb69e74c59c"
        self.assertEqual(known_good_hash, calculate_hash_of_file(test))
        os.unlink(test)


if __name__ == "__main__":
    unittest.main()
    # pass

## Code used to create test:
# pdf = fpdf.FPDF()
# pdf.compress = False
# pdf.add_page()
# png = "https://g.twimg.com/Twitter_logo_blue.png"
# pdf.image(png, x = 15, y = 15, w = 30, h = 25)

# test = relative_path_to('output.pdf')

# set_doc_date_0(pdf)
# pdf.output(test, 'F')

# print(calculate_hash_of_file(test))
# os.unlink(test)

# pdf = fpdf.FPDF()
# pdf.compress = False
# pdf.add_page()
# jpg = ("https://upload.wikimedia.org/wikipedia/commons/8/8c/"
#        "JPEG_example_JPG_RIP_025.jpg")
# pdf.image(jpg, x = 15, y = 15)

# test = relative_path_to('output.pdf')

# set_doc_date_0(pdf)
# pdf.output(test, 'F')

# print(calculate_hash_of_file(test))
# os.unlink(test)
