import unittest
import sys

import fpdf
from PIL import Image
from test.utilities import assert_pdf_equal, relative_path_to

# python -m unittest test.image.image_types.insert_images


class InsertImagesTest(unittest.TestCase):
    def test_insert_jpg(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = relative_path_to("insert_images_insert_jpg.jpg")
        pdf.image(file_path, x=15, y=15, h=140)
        if sys.platform in ("cygwin", "win32"):
            # Pillow uses libjpeg-turbo on Windows and libjpeg elsewhere,
            # leading to a slightly different image being parsed and included in the PDF:
            assert_pdf_equal(self, pdf, "image_types_insert_jpg_windows.pdf")
        else:
            assert_pdf_equal(self, pdf, "image_types_insert_jpg.pdf")

    def test_insert_png(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = relative_path_to("insert_images_insert_png.png")
        pdf.image(file_path, x=15, y=15, h=140)
        assert_pdf_equal(self, pdf, "image_types_insert_png.pdf")

    def test_insert_bmp(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = relative_path_to("circle.bmp")
        pdf.image(file_path, x=15, y=15, h=140)
        assert_pdf_equal(self, pdf, "image_types_insert_bmp.pdf")

    def test_insert_gif(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = relative_path_to("circle.gif")
        pdf.image(file_path, x=15, y=15)
        assert_pdf_equal(self, pdf, "image_types_insert_gif.pdf")

    def test_insert_pillow(self):
        pdf = fpdf.FPDF()
        pdf.add_page()
        file_path = relative_path_to("insert_images_insert_png.png")
        img = Image.open(file_path)
        pdf.image(img, x=15, y=15)
        assert_pdf_equal(self, pdf, "image_types_insert_pillow.pdf")


if __name__ == "__main__":
    unittest.main()
