import sys
from pathlib import Path

import fpdf
from PIL import Image
from test.utilities import assert_pdf_equal


HERE = Path(__file__).resolve().parent


class TestInsertImages:
    def test_insert_jpg(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = HERE / "insert_images_insert_jpg.jpg"
        pdf.image(file_path, x=15, y=15, h=140)
        if sys.platform in ("cygwin", "win32"):
            # Pillow uses libjpeg-turbo on Windows and libjpeg elsewhere,
            # leading to a slightly different image being parsed and included in the PDF:
            assert_pdf_equal(pdf, HERE / "image_types_insert_jpg_windows.pdf", tmp_path)
        else:
            assert_pdf_equal(pdf, HERE / "image_types_insert_jpg.pdf", tmp_path)

    def test_insert_png(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = HERE / "insert_images_insert_png.png"
        pdf.image(file_path, x=15, y=15, h=140)
        assert_pdf_equal(pdf, HERE / "image_types_insert_png.pdf", tmp_path)

    def test_insert_bmp(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = HERE / "circle.bmp"
        pdf.image(file_path, x=15, y=15, h=140)
        assert_pdf_equal(pdf, HERE / "image_types_insert_bmp.pdf", tmp_path)

    def test_insert_gif(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.compress = False
        pdf.add_page()
        file_path = HERE / "circle.gif"
        pdf.image(file_path, x=15, y=15)
        assert_pdf_equal(pdf, HERE / "image_types_insert_gif.pdf", tmp_path)

    def test_insert_pillow(self, tmp_path):
        pdf = fpdf.FPDF()
        pdf.add_page()
        file_path = HERE / "insert_images_insert_png.png"
        img = Image.open(file_path)
        pdf.image(img, x=15, y=15)
        assert_pdf_equal(pdf, HERE / "image_types_insert_pillow.pdf", tmp_path)
