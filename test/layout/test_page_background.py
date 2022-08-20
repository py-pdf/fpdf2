from fpdf import FPDF, drawing
from PIL import Image
import io
from pathlib import Path
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
imgpath = str(HERE / "../image/image_types/insert_images_insert_jpg.jpg")


def rgb_tuple_multi_page(pdf, fill_set=None):
    """
    sets the background using a tuple representing an RGB color and adds a page with text and a small rectangle,
    then writes multiline-text to trigger a page break to test if the background color is retained
    """
    pdf.set_page_background((170, 200, 100))
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 30, 'RGB tuple', align='R', border=1)
    pdf.ln()
    if fill_set:
        pdf.cell(0, 30, 'fill color set', align='R', fill=True)
    else:
        pdf.cell(0, 30, 'default fill color', align='R')
    pdf.ln()
    pdf.multi_cell(0, pdf.h/2, 'PAGE 1\nPAGE 2')

def DeviceRGB_page(pdf):
    """sets the background using an instance of DeviceRGB and adds a page with text and a small rectangle"""
    pdf.set_page_background(drawing.DeviceRGB(0.2, 0.4, 0.1))
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 10, 'DeviceRGB', align='R', border=1)

def imgpath_str_page(pdf, fill_set=None):
    """
    sets the background to an image specified with a path and adds a page with text and a small rectangle,
    then writes multi-line text to trigger a page break to test if the background image is retained
    """
    pdf.set_page_background(imgpath)
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 10, 'Image file path', align='R', border=1)
    pdf.ln()
    pdf.multi_cell(0,  pdf.h/2, 'PAGE 1\nPAGE 2')

def imglink_str_page(pdf):
    """sets the background to an image specified with a link and adds a page with text and a small rectangle"""
    pdf.set_page_background('https://raw.githubusercontent.com/PyFPDF/fpdf2/master/test/image/image_types/insert_images_insert_jpg.jpg')
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 10, 'Image file link', align='R', border=1)

def PILimg_page(pdf):
    """sets the background using an instance of PIL.Image.Image and adds a page with text and a small rectangle"""
    img = Image.open(imgpath)
    pdf.set_page_background(img)
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 10, 'PIL.Image.Image', align='R', border=1)

def ioBytesIO_page(pdf):
    """sets the background using an instance of io.BytesIO of an image and adds a page with text and a small rectangle"""
    with open(imgpath, 'rb') as f:
        buffer = io.BytesIO(f.read())
    pdf.set_page_background(buffer)
    pdf.add_page()
    pdf.rect(20, 20, 60, 60, style='F')
    pdf.cell(0, 10, 'io.BytesIO', align='R', border=1)


def test_page_background(tmp_path):
    """
    Test creating a PDF with multiple pages using all possible inputs to set a page background,
    drawing a rectangle and writing text on every page, testing if any other color is overwritten,
    writing a multi-line text to test if the background is retained on an automatic page break,
    then setting a fill color, testing if the background color gets overriden and vice versa
    by printing another two pages with a background color and image
    """
    pdf = FPDF()
    pdf.set_font('Helvetica', 'B', 30)
    rgb_tuple_multi_page(pdf)
    imgpath_str_page(pdf)
    DeviceRGB_page(pdf)
    imglink_str_page(pdf)
    PILimg_page(pdf)
    ioBytesIO_page(pdf) 


    pdf.set_fill_color(255, 200, 210)
    rgb_tuple_multi_page(pdf, fill_set=True)
    imgpath_str_page(pdf)

    assert_pdf_equal(pdf, HERE / "page_background.pdf", tmp_path, generate=True)