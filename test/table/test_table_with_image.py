from pathlib import Path

import pytest

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
    ("Multilines text", "Image"),
    (LOREM_IPSUM[:200], IMG_DIR / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"),
    (LOREM_IPSUM[200:400], IMG_DIR / "png_images/ac6343a98f8edabfcc6e536dd75aacb0.png"),
    (LOREM_IPSUM[400:600], IMG_DIR / "image_types/insert_images_insert_png.png"),
    (LOREM_IPSUM[600:800], IMG_DIR / "image_types/circle.bmp"),
)


def test_table_with_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for i, data_row in enumerate(TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 2 and i > 0:
                    row.cell(img=datum)
                else:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_images.pdf", tmp_path)


def test_table_with_images_and_img_fill_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for i, data_row in enumerate(TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 2 and i > 0:
                    row.cell(img=datum, img_fill_width=True)
                else:
                    row.cell(datum)
    assert_pdf_equal(
        pdf,
        HERE / "table_with_images_and_img_fill_width.pdf",
        tmp_path,
    )


def test_table_with_multiline_cells_and_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for i, data_row in enumerate(MULTILINE_TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 1 and i > 0:
                    row.cell(img=datum, img_fill_width=True)
                else:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_multiline_cells_and_images.pdf", tmp_path)


def test_table_with_images_and_text():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(NotImplementedError):
        with pdf.table() as table:
            for i, data_row in enumerate(TABLE_DATA):
                row = table.row()
                for j, datum in enumerate(data_row):
                    if j == 2 and i > 0:
                        row.cell(datum.name, img=datum)
                    else:
                        row.cell(datum)
