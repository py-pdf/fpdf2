from pathlib import Path

import pytest

import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.skip("skip network tests by default")
def test_png_url(tmp_path):
    pdf = fpdf.FPDF()
    pdf.compress = False
    pdf.add_page()
    png = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
    pdf.image(png, x=15, y=15, w=30, h=25)
    assert_pdf_equal(pdf, HERE / "image_png_url.pdf", tmp_path)


@pytest.mark.skip("skip network tests by default")
def test_jpg_url(tmp_path):
    pdf = fpdf.FPDF()
    pdf.compress = False
    pdf.add_page()
    jpg = (
        "https://upload.wikimedia.org/wikipedia/commons/8/8c/"
        "JPEG_example_JPG_RIP_025.jpg"
    )
    pdf.image(jpg, x=15, y=15)
    assert_pdf_equal(pdf, HERE / "image_jpg_url.pdf", tmp_path)


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
