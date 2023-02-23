from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal, LOREM_IPSUM


HERE = Path(__file__).resolve().parent
IMG_DIR = HERE.parent / "image"

TABLE_DATA = (
    ("First name", "Last name", "Image", "City"),
    (
        "Jules",
        "Smith",
        IMG_DIR / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png",
        "San Juan",
    ),
    (
        "Mary",
        "Ramos",
        IMG_DIR / "png_images/ac6343a98f8edabfcc6e536dd75aacb0.png",
        "Orlando",
    ),
    (
        "Carlson",
        "Banks",
        IMG_DIR / "image_types/insert_images_insert_png.png",
        "Los Angeles",
    ),
    ("Lucas", "Cimon", IMG_DIR / "image_types/circle.bmp", "Angers"),
)
MULTILINE_TABLE_DATA = (
    ("Extract", "Text length"),
    (LOREM_IPSUM[:200], str(len(LOREM_IPSUM[:200]))),
    (LOREM_IPSUM[200:400], str(len(LOREM_IPSUM[200:400]))),
    (LOREM_IPSUM[400:600], str(len(LOREM_IPSUM[400:600]))),
    (LOREM_IPSUM[600:800], str(len(LOREM_IPSUM[600:800]))),
    (LOREM_IPSUM[800:1000], str(len(LOREM_IPSUM[800:1000]))),
    (LOREM_IPSUM[1000:1200], str(len(LOREM_IPSUM[1000:1200]))),
)


def test_table_with_an_image(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for i, data_row in enumerate(TABLE_DATA):
            with table.row() as row:
                for j, datum in enumerate(data_row):
                    if j == 2 and i > 0:
                        row.cell(img=datum)
                    else:
                        row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_an_image.pdf", tmp_path)


def test_table_with_an_image_and_img_fill_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for i, data_row in enumerate(TABLE_DATA):
            with table.row() as row:
                for j, datum in enumerate(data_row):
                    if j == 2 and i > 0:
                        row.cell(img=datum, img_fill_width=True)
                    else:
                        row.cell(datum)
    assert_pdf_equal(
        pdf,
        HERE / "table_with_an_image_and_img_fill_width.pdf",
        tmp_path,
    )
