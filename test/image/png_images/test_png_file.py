from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_insert_png_files(caplog, tmp_path):
    pdf = FPDF()
    for path in sorted(HERE.glob("*.png")):
        pdf.add_page()
        pdf.image(str(path), x=0, y=0, w=0, h=0)
    # Note: 7 of those images have an ICC profile, and there are only 5 distinct ICC profiles among them
    assert_pdf_equal(pdf, HERE / "image_png_insert_png_files.pdf", tmp_path)

    assert "Unsupported color space CMYK in ICC Profile of file" in caplog.text
    # Note: the warning above comes from the following files, for which ImageMagics also raise warnings:
    #   identify-im6.q16: iCCP: profile 'icc': 'CMYK': invalid ICC profile color space `test/image/png_images/0839d93f8e77e21acd0ac40a80b14b7b.png'
    #   identify-im6.q16: iCCP: profile 'icc': 'CMYK': invalid ICC profile color space `test/image/png_images/1ebd73c1d3fbc89782f29507364128fc.png'
