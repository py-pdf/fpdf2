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
from test.utilities import assert_pdf_equal, relative_path_to

# python -m unittest test.image.image_types.insert_images


class InsertImagesTest(unittest.TestCase):
    def test_insert_jpg(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("insert_images_insert_jpg.jpg")
        pdf.image(imagename, x=15, y=15, h=140)
        if sys.platform in ("cygwin", "win32"):
            # Pillow uses libjpeg-turbo on Windows and libjpeg elsewhere,
            # leading to a slightly different image being parsed and included in the PDF:
            assert_pdf_equal(self, pdf, "test_insert_jpg_windows.pdf")
        else:
            assert_pdf_equal(self, pdf, "test_insert_jpg.pdf")

    def test_insert_png(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("insert_images_insert_png.png")
        pdf.image(imagename, x=15, y=15, h=140)
        assert_pdf_equal(self, pdf, "test_insert_png.pdf")

    def test_insert_bmp(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("circle.bmp")
        pdf.image(imagename, x=15, y=15, h=140)
        assert_pdf_equal(self, pdf, "test_insert_bmp.pdf")

    def test_insert_gif(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("circle.gif")
        pdf.image(imagename, x=15, y=15)
        assert_pdf_equal(self, pdf, "test_insert_gif.pdf")


if __name__ == "__main__":
    unittest.main()
