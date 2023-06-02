from pathlib import Path

import qrcode, pytest

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, YPos, TableCellFillMode
from fpdf.fonts import FontFace
from test.conftest import assert_pdf_equal, LOREM_IPSUM

def show(pdf):
    pdf.output(r'c:\data\temp.pdf')
    import subprocess
    subprocess.Popen(r'explorer "c:\data\temp.pdf"')


HERE = Path(__file__).resolve().parent
IMG_DIR = HERE.parent / "image"

IMAGE = IMG_DIR / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png"

IMAGES_DATA = (
    (IMAGE, IMAGE, IMAGE, IMAGE),
    (IMAGE, IMAGE, IMAGE, IMAGE),
    (IMAGE, IMAGE, IMAGE, IMAGE),
    (IMAGE, IMAGE, IMAGE, IMAGE),
)

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
    ("Brave Sir Robin ", "the  Not-Quite-So-Brave-As-Sir-Lancelot", "+", "Bridge of Death"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),

)

LONG_TEXT = """
Professor: (Eric Idle) It's an entirely new strain of sheep, a killer sheep that can not only hold a rifle but is also a first-class shot.
Assistant: But where are they coming from, professor?
Professor: That I don't know. I just don't know. I really just don't know. I'm afraid I really just don't know. I'm afraid even I really just don't know. I have to tell you I'm afraid even I really just don't know. I'm afraid I have to tell you... (she hands him a glass of water which she had been busy getting as soon as he started into this speech) ... thank you ... (resuming normal breezy voice) ... I don't know. Our only clue is this portion of wolf's clothing which the killer sheep ..."""

SHORT_TEXT = "Monty Python / Killer Sheep"

TWO_LINE_TEXT = "Monty Python\nKiller Sheep"

# def test_multicell_with_padding():
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Times", size=16)
#     pdf.multi_cell(0, 5, LONG_TEXT, border = 1, padding = (10, 20, 30, 40))
#
#     pdf.x = 0
#     pdf.y = 0
#     pdf.multi_cell(150, 5, SHORT_TEXT, border = 1, padding = (5, 5, 5, 5))
#
#     pdf.output(HERE / "multicell_with_padding.pdf")
#
#     import subprocess
#     subprocess.Popen('explorer "' + str(HERE / "multicell_with_padding.pdf") + '"' )

def test_multicell_with_padding_check_input():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    with pytest.raises(ValueError):
        pdf.multi_cell(0, 5, LONG_TEXT, border = 1, padding = (5, 5, 5, 5,5,5))

def test_multicell_return_value():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    pdf.x = 5

    out = pdf.multi_cell(0, 5, TWO_LINE_TEXT, border=1, padding=0, output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,)
    print(out)
    height_without_padding = out[1]

    pdf.x = 5
    # pdf.y += 50

    # try again
    out = pdf.multi_cell(0, 5, TWO_LINE_TEXT, border=1, padding=0,
                         output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT, )

    height_without_padding2 = out[1]

    pdf.x = 5
    # pdf.y += 50

    # try again
    out = pdf.multi_cell(0, 5, TWO_LINE_TEXT, border=1, padding=10,
                         output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT, )

    height_with_padding = out[1]




    assert height_without_padding == height_without_padding2
    assert height_without_padding + 20 == height_with_padding

    pdf.x = 5
    pdf.y += 10

    old_y = pdf.y
    out = pdf.multi_cell(0, 5, TWO_LINE_TEXT, border=1, padding=10,
                         output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT, new_y = YPos.NEXT)

    # assert pdf.y == old_y + height_with_padding


    pdf.output(HERE / "table_with_padding.pdf")

    import subprocess
    subprocess.Popen('explorer "' + str(HERE / "table_with_padding.pdf") + '"')


def test_table_with_multiline_cells_and_images_padding_and_pagebreak(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)

    with pdf.table(line_height = pdf.font_size, padding = (5,5,5,5),col_widths= (0.3,0.2), width = 80) as table:
        for i, data_row in enumerate(MULTILINE_TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 1 and i > 0:
                    row.cell(img=datum, img_fill_width=False, style = deathstyle)
                else:
                    row.cell(datum)
    # assert_pdf_equal(pdf, HERE / "table_with_multiline_cells_and_images.pdf", tmp_path)
    show(pdf)

def test_table_with_only_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table(line_height=pdf.font_size,
                   padding=(5, 7, 3, 4),
                   width = 120,
                   col_widths = (1,2,3,2),
                   cell_fill_color=(150, 200, 255),
                   cell_fill_mode = TableCellFillMode.ROWS,
                   ) as table:
        for i, data_row in enumerate(IMAGES_DATA):
            row = table.row()
            for datum in data_row:
                row.cell(img=datum)


    show(pdf)





def test_table_simple_padding(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)

    with pdf.table(line_height = pdf.font_size,padding=3) as table:
        for data_row in TABLE_DATA:
            row = table.row()
            for datum in data_row:
                if "Death" in datum:
                    row.cell(datum, style=deathstyle)
                else:
                    row.cell(datum)
    # assert_pdf_equal(pdf, HERE / "table_simple.pdf", tmp_path)
    show(pdf)

def test_padding_per_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)

    with pdf.table(line_height = pdf.font_size,padding=2) as table:
        for irow in range(5):
            row = table.row()
            for icol in range(5):
                datum = "Circus"

                if irow == 3 and icol %2 == 0:
                    row.cell("custom padding", style=deathstyle, padding = (2*icol,8,8,8))
                else:
                    row.cell(datum)
    # assert_pdf_equal(pdf, HERE / "table_simple.pdf", tmp_path)
    show(pdf)

def test_draw_box():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    pdf._draw_box( 0, 0, 40, 20, 1, False)

    show(pdf)