from pathlib import Path

import qrcode, pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent
IMG_DIR = HERE.parent / "image"



MULTILINE_TABLE_DATA = (
    ("Multilines text", "Image"),
    (LOREM_IPSUM[:200], IMG_DIR / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"),
    (LOREM_IPSUM[200:400], IMG_DIR / "png_images/ac6343a98f8edabfcc6e536dd75aacb0.png"),
    (LOREM_IPSUM[400:600], IMG_DIR / "image_types/insert_images_insert_png.png"),
    (LOREM_IPSUM[600:800], IMG_DIR / "image_types/circle.bmp"),
)

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),

)

LONG_TEXT = """
Professor: (Eric Idle) It's an entirely new strain of sheep, a killer sheep that can not only hold a rifle but is also a first-class shot.
Assistant: But where are they coming from, professor?
Professor: That I don't know. I just don't know. I really just don't know. I'm afraid I really just don't know. I'm afraid even I really just don't know. I have to tell you I'm afraid even I really just don't know. I'm afraid I have to tell you... (she hands him a glass of water which she had been busy getting as soon as he started into this speech) ... thank you ... (resuming normal breezy voice) ... I don't know. Our only clue is this portion of wolf's clothing which the killer sheep ..."""

SHORT_TEXT = "Monty Python / Killer Sheep"

def test_multicell_with_padding():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.multi_cell(0, 5, LONG_TEXT, border = 1, padding = (10, 20, 30, 40))

    pdf.x = 45
    pdf.y += 50
    pdf.multi_cell(150, 5, SHORT_TEXT, border = 1, padding = (5, 5, 5, 5))

    pdf.output(HERE / "multicell_with_padding.pdf")

    import subprocess
    subprocess.Popen('explorer "' + str(HERE / "multicell_with_padding.pdf") + '"' )

def test_multicell_with_padding_check_input():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    with pytest.raises(ValueError):
        pdf.multi_cell(0, 5, LONG_TEXT, border = 1, padding = (5, 5, 5, 5,5,5))



def test_table_with_multiline_cells_and_images_padding(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table(line_height = pdf.font_size, padding = (5,5,5,5)) as table:
        for i, data_row in enumerate(MULTILINE_TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 1 and i > 0:
                    row.cell(img=datum, img_fill_width=True)
                else:
                    row.cell(datum)
    # assert_pdf_equal(pdf, HERE / "table_with_multiline_cells_and_images.pdf", tmp_path)
    pdf.output(HERE / "table_with_padding.pdf")

    import subprocess
    subprocess.Popen('explorer "' + str(HERE / "table_with_padding.pdf") + '"' )


def test_table_simple_padding(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)
    with pdf.table(padding=2) as table:
        for data_row in TABLE_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(datum)
    # assert_pdf_equal(pdf, HERE / "table_simple.pdf", tmp_path)
    pdf.output(HERE / "simple_table_with_padding.pdf")

    import subprocess
    subprocess.Popen('explorer "' + str(HERE / "simple_table_with_padding.pdf") + '"')