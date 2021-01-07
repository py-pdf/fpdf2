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

# python -m unittest test.image.image_types.insert_images.InsertImagesTest


class InsertImagesTest(unittest.TestCase):
    def test_insert_jpg(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("insert_images_insert_jpg.jpg")
        pdf.image(imagename, x=15, y=15, h=140)

        set_doc_date_0(pdf)
        output_file = relative_path_to("insert_images_jpg_test.pdf")
        pdf.output(output_file, "F")

        test_hash = calculate_hash_of_file(output_file)
        self.assertEqual(test_hash, "98e21803d01d686504238cb17a636c32")
        os.unlink(output_file)

    def test_insert_png(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("insert_images_insert_png.png")
        pdf.image(imagename, x=15, y=15, h=140)

        set_doc_date_0(pdf)
        test = relative_path_to("insert_images_png_test.pdf")
        pdf.output(test, "F")

        test_hash = calculate_hash_of_file(test)
        self.assertEqual(test_hash, "17c98e10f5c0d95ae17cd31b0f6a0919")
        os.unlink(test)

    def test_insert_bmp(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("circle.bmp")
        pdf.image(imagename, x=15, y=15, h=140)

        set_doc_date_0(pdf)
        test = relative_path_to("insert_images_bmp_test.pdf")
        pdf.output(test, "F")

        test_hash = calculate_hash_of_file(test)
        self.assertEqual(test_hash, "49e5800162c7b019ac25354ce4708e35")
        os.unlink(test)

    def test_insert_gif(self):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        imagename = relative_path_to("circle.gif")
        pdf.image(imagename, x=15, y=15)

        set_doc_date_0(pdf)
        test = relative_path_to("insert_images_gif_test.pdf")
        pdf.output(test, "F")

        test_hash = calculate_hash_of_file(test)
        self.assertEqual(test_hash, "be9994a5fadccca9d316c39d302f6248")
        os.unlink(test)


if __name__ == "__main__":
    unittest.main()

## Code used to create test:
# doc = fpdf.FPDF()
# doc.compress = False
# doc.add_page()
# imagename = relative_path_to('insert_images_insert_jpg.jpg')
# doc.image(imagename, x = 15, y = 15, h = 140) #, w = 30, h = 25)
# set_doc_date_0(doc)
# output_name = relative_path_to('insert_images_jpg_good.pdf')
# doc.output(output_name)
# print calculate_hash_of_file(output_name)

# doc = fpdf.FPDF()
# doc.compress = False
# doc.add_page()
# imagename = relative_path_to('insert_images_insert_png.png')
# doc.image(imagename, x = 15, y = 15, h = 140) #, w = 30, h = 25)
# set_doc_date_0(doc)
# output_name = relative_path_to('insert_images_png_good.pdf')
# doc.output(output_name)
# print calculate_hash_of_file(output_name)
