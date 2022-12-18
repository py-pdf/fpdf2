from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_insert_png_files(tmp_path):
    pdf = fpdf.FPDF(unit="pt")
    pdf.compress = False

    not_supported = {
        "e59ec0cfb8ab64558099543dc19f8378.png",  # Interlacing not supported:
        "6c853ed9dacd5716bc54eb59cec30889.png",  # 16-bit depth not supported:
        "ac6343a98f8edabfcc6e536dd75aacb0.png",  # Interlacing not supported:
        "93e6127b9c4e7a99459c558b81d31bc5.png",  # Interlacing not supported:
        "18f9baf3834980f4b80a3e82ad45be48.png",  # Interlacing not supported:
        "51a4d21670dc8dfa8ffc9e54afd62f5f.png",  # Interlacing not supported:
    }

    for path in sorted(HERE.glob("*.png")):
        if path.name not in not_supported:
            pdf.add_page()
            pdf.image(str(path), x=0, y=0, w=0, h=0)

    assert_pdf_equal(pdf, HERE / "image_png_insert_png_files.pdf", tmp_path)
