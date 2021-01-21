import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..", "..")
    ),
)

import fpdf
from test.utilities import assert_pdf_equal

# python -m unittest test.image.url_images


@pytest.mark.skip("skip network tests by default")
class TestUrlImages:
    def test_png_url(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        png = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
        pdf.image(png, x=15, y=15, w=30, h=25)
        assert_pdf_equal(self, pdf, "image_png_url.pdf")

    def test_jpg_url(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        jpg = (
            "https://upload.wikimedia.org/wikipedia/commons/8/8c/"
            "JPEG_example_JPG_RIP_025.jpg"
        )
        pdf.image(jpg, x=15, y=15)
        assert_pdf_equal(self, pdf, "image_jpg_url.pdf")


## Code used to create test:
# pdf = fpdf.FPDF()
# pdf.compress = False
# pdf.add_page()
# png = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
# pdf.image(png, x = 15, y = 15, w = 30, h = 25)

# test = relative_path_to('output.pdf')

# set_doc_date_0(pdf)
# pdf.output(test)

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
# pdf.output(test)

# print(calculate_hash_of_file(test))
# os.unlink(test)
