from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, YPos, TableCellFillMode, VAlign
from fpdf.fonts import FontFace
from fpdf.table import draw_box_borders

from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def run_comparison(pdf, name, tmp_path, **kwargs):
    filename = HERE / f"{name}.pdf"
    assert_pdf_equal(pdf, filename, tmp_path, **kwargs)


IMG_DIR = HERE.parent / "image"

IMAGE = IMG_DIR / "image_types/pythonknight.png"

IMAGES_DATA = (
    (IMAGE, IMAGE, IMAGE, IMAGE),
    (IMAGE, IMAGE, IMAGE, IMAGE),
    (IMAGE, IMAGE, IMAGE, IMAGE),
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
    (
        "Brave Sir Robin ",
        "the  Not-Quite-So-Brave-As-Sir-Lancelot",
        "+",
        "Bridge of Death",
    ),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
)

LONG_TEXT = (
    "\nProfessor: (Eric Idle) It's an entirely new strain of sheep, a killer sheep that can not only hold a rifle but is also a first-class shot.\n"
    "Assistant: But where are they coming from, professor?\n"
    "Professor: That I don't know. I just don't know. I really just don't know. I'm afraid I really just don't know. I'm afraid even I really just"
    " don't know. I have to tell you I'm afraid even I really just don't know. I'm afraid I have to tell you... (she hands him a glass of water"
    " which she had been busy getting as soon as he started into this speech) ... thank you ... (resuming normal breezy voice) ... I don't know."
    " Our only clue is this portion of wolf's clothing which the killer sheep ..."
)


TABLE_DATA_LIST = ["And", "now", "for", "something", "completely", "different"]

SHORT_TEXT = "Monty Python / Killer Sheep"

TWO_LINE_TEXT = "Monty Python\nKiller Sheep"


def test_multicell_with_padding(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.multi_cell(0, 5, LONG_TEXT, border=1, padding=(10, 20, 30, 40))

    run_comparison(pdf, "multicell_with_padding", tmp_path)


def test_multicell_with_padding_check_input():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    with pytest.raises(ValueError):
        pdf.multi_cell(0, 5, LONG_TEXT, border=1, padding=(5, 5, 5, 5, 5, 5))


def test_multicell_return_value(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    pdf.x = 5

    out = pdf.multi_cell(
        0,
        5,
        TWO_LINE_TEXT,
        border=1,
        padding=0,
        output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
    )
    height_without_padding = out[1]

    pdf.x = 5
    # pdf.y += 50

    # try again
    out = pdf.multi_cell(
        0,
        5,
        TWO_LINE_TEXT,
        border=1,
        padding=0,
        output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
    )

    height_without_padding2 = out[1]

    pdf.x = 5
    # pdf.y += 50

    # try again
    out = pdf.multi_cell(
        0,
        5,
        TWO_LINE_TEXT,
        border=1,
        padding=10,
        output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
    )

    height_with_padding = out[1]

    assert height_without_padding == height_without_padding2
    assert height_without_padding + 20 == height_with_padding

    pdf.x = 5
    pdf.y += 10

    out = pdf.multi_cell(
        0,
        5,
        TWO_LINE_TEXT,
        border=1,
        padding=10,
        output=MethodReturnValue.PAGE_BREAK | MethodReturnValue.HEIGHT,
        new_y=YPos.NEXT,
    )

    run_comparison(pdf, "table_with_padding", tmp_path)


def test_table_with_multiline_cells_and_images_padding_and_pagebreak(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)

    with pdf.table(
        line_height=pdf.font_size,
        padding=(5, 5, 5, 5),
        col_widths=(0.3, 0.2),
        width=80,
        outer_border_width=3,
    ) as table:
        for i, data_row in enumerate(MULTILINE_TABLE_DATA):
            row = table.row()
            for j, datum in enumerate(data_row):
                if j == 1 and i > 0:
                    row.cell(img=datum, img_fill_width=False, style=deathstyle)
                else:
                    row.cell(datum)

    run_comparison(
        pdf, "table_with_multiline_cells_and_images_padding_and_pagebreak", tmp_path
    )


def test_table_with_single_row_of_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.text(60, 100, "All these images should be the same size")
    with pdf.table(
        line_height=pdf.font_size,
        padding=(5, 7, 3, 4),
        width=120,
        col_widths=(2, 2, 2, 2),
        cell_fill_color=(150, 200, 255),
        cell_fill_mode=TableCellFillMode.ROWS,
    ) as table:
        data_row = IMAGES_DATA[0]
        row = table.row()
        for datum in data_row:
            row.cell(img=datum)

    run_comparison(pdf, "table_with_single_row_of_images", tmp_path)


def test_table_with_only_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table(
        line_height=pdf.font_size,
        padding=(5, 7, 3, 4),
        width=120,
        col_widths=(1, 2, 3, 2),
        cell_fill_color=(150, 200, 255),
        cell_fill_mode=TableCellFillMode.ROWS,
    ) as table:
        for data_row in IMAGES_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(img=datum)

    run_comparison(pdf, "table_with_only_images", tmp_path)


def test_table_vertical_alignment(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    red = (255, 100, 100)
    black = (0, 0, 0)

    pdf.rect(pdf.l_margin, pdf.t_margin, pdf.epw, pdf.eph)
    pdf.rect(0, pdf.t_margin, pdf.l_margin, pdf.eph)
    pdf.rect(pdf.l_margin + pdf.epw, pdf.t_margin, pdf.r_margin, pdf.eph)
    # pdf.rect(0, pdf.t_margin, pdf.l_margin, pdf.eph)

    deathstyle = FontFace(color=black, fill_color=red)
    # write_html() doesn't add a nl at the very top of the page anymore.
    pdf.ln(0.1)

    for v in (VAlign.T, VAlign.M, VAlign.B):
        pdf.write_html(f"<h1>Vertical alignment: {v}</h1>")

        with pdf.table(line_height=pdf.font_size, padding=3, v_align=v) as table:
            for data_row in TABLE_DATA:
                row = table.row()
                for datum in data_row:
                    if "Death" in datum:
                        row.cell(datum, style=deathstyle)
                    else:
                        row.cell(datum)

    run_comparison(pdf, "table_vertical_alignment", tmp_path)


def test_padding_per_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)
    with pdf.table(line_height=pdf.font_size, padding=2) as table:
        for irow in range(5):
            row = table.row()
            for icol in range(5):
                datum = "Circus"
                if irow == 3 and icol % 2 == 0:
                    row.cell(
                        "custom padding", style=deathstyle, padding=(2 * icol, 8, 8, 8)
                    )
                else:
                    row.cell(datum)

    run_comparison(pdf, "table_padding_per_cell", tmp_path)


def test_valign_per_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    red = (255, 100, 100)
    black = (0, 0, 0)

    deathstyle = FontFace(color=black, fill_color=red)

    with pdf.table(line_height=pdf.font_size, padding=2, v_align=VAlign.M) as table:
        for irow in range(5):
            row = table.row()
            for icol in range(5):
                datum = icol * "Circus\n"

                if irow == 2:
                    v_align = VAlign.T
                elif irow == 3:
                    v_align = VAlign.B

                if irow in (2, 3):
                    row.cell(
                        f"{datum}: custom v-align {v_align}",
                        style=deathstyle,
                        v_align=v_align,
                    )
                else:
                    row.cell(datum)

    run_comparison(pdf, "table_valign_per_cell", tmp_path)


def test_table_with_gutter_and_padding_and_outer_border_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table(
        TABLE_DATA,
        gutter_height=3,
        gutter_width=5,
        line_height=pdf.font_size,
        align="L",
        outer_border_width=2,
    ):
        pass

    run_comparison(
        pdf, "table_with_gutter_and_padding_and_outer_border_width", tmp_path
    )


def test_table_with_colspan(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    def make_text(n):
        a = TABLE_DATA_LIST[int(n / 2) % len(TABLE_DATA_LIST)]
        b = TABLE_DATA_LIST[(int(n**2 * 10) + 4) % len(TABLE_DATA_LIST)]

        if n % 4 == 0:
            return f"{a} {b}"
        if n % 4 == 1:
            return f"{a} {b} {a}"
        if n % 4 == 2:
            return f"{b} {a}"

        return a

    with pdf.table(line_height=pdf.font_size, gutter_height=3, gutter_width=3) as table:
        for irow in range(10):
            row = table.row()
            for icol in range(10):
                txt = make_text(irow * 10 + icol)
                txt = str(icol) + " " + txt
                if irow > 0:
                    if icol == 2:
                        row.cell(txt + " SPAN 2", colspan=2)
                        continue
                    if icol == 3:
                        continue
                row.cell(txt)

    run_comparison(pdf, "table_with_colspan", tmp_path)


def test_outside_border_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    with pdf.table(outer_border_width=1, gutter_height=10, gutter_width=15) as table:
        for _ in range(5):
            row = table.row()
            for _ in range(5):
                datum = "Circus"
                row.cell(datum)

    run_comparison(pdf, "table_with_outside_border_width", tmp_path)


def test_table_colspan_and_padding(tmp_path):
    pdf = FPDF()

    pdf.set_font("Times", size=12)
    pdf.add_page()
    with pdf.table(col_widths=(1, 2, 1, 1), padding=5) as table:
        row = table.row()
        row.cell("0")
        row.cell("1")
        row.cell("2")
        row.cell("3")
        row = table.row()
        row.cell("A1")
        row.cell("A2", colspan=2)
        # row.cell("void") # <--- this cell is not rendered
        row.cell("A4")

        row = table.row()
        row.cell("B1", colspan=2)
        # row.cell("void")  # <--- this cell is not rendered
        row.cell("B3")
        row.cell("B4")

    pdf.c_margin = 10

    with pdf.table(col_widths=(1, 2, 1, 1), padding=5) as table:
        row = table.row()
        row.cell("0")
        row.cell("1")
        row.cell("2")
        row.cell("3")
        row = table.row()
        row.cell("A1")
        row.cell("A2", colspan=2)
        # row.cell("void")  # <--- this cell is not rendered
        row.cell("A4")

        row = table.row()
        row.cell("B1", colspan=2)
        # row.cell("void")  # <--- this cell is not rendered
        row.cell("B3")
        row.cell("B4")

    run_comparison(pdf, "table_colspan_and_padding", tmp_path)


def test_table_colspan_and_padding_and_gutter(tmp_path):
    pdf = FPDF()

    pdf.set_font("Times", size=12)
    pdf.add_page()
    with pdf.table(
        col_widths=(1, 2, 1, 1), padding=5, gutter_height=3, gutter_width=5
    ) as table:
        row = table.row()
        row.cell("0")
        row.cell("1")
        row.cell("2")
        row.cell("3")
        row = table.row()
        row.cell("A1")
        row.cell("A2", colspan=2)
        row.cell("A4")

        row = table.row()
        row.cell("B1", colspan=2)
        row.cell("B3")
        row.cell("B4")

    run_comparison(pdf, "table_colspan_and_padding_and_gutter", tmp_path)


def test_table_colspan_and_padding_and_gutter_and_width(tmp_path):
    pdf = FPDF()

    pdf.set_font("Times", size=12)
    pdf.add_page()
    with pdf.table(
        col_widths=(1, 2, 1, 1), padding=5, gutter_height=3, gutter_width=5, width=100
    ) as table:
        row = table.row()
        row.cell("0")
        row.cell("1")
        row.cell("2")
        row.cell("3")
        row = table.row()
        row.cell("A1")
        row.cell("A2,3,4", colspan=3)

        row = table.row()
        row.cell("B1", colspan=2)
        row.cell("B3")
        row.cell("B4")

    run_comparison(pdf, "table_colspan_and_padding_and_gutter_and_width", tmp_path)


def test_table_with_cell_overflow(tmp_path):
    pdf = FPDF()
    pdf.set_font("Times", size=30)
    pdf.add_page()

    boldstyle = FontFace("Times", emphasis="B")

    with pdf.table(width=pdf.epw / 2, col_widths=(1, 2, 1)) as table:
        row = table.row()
        row.cell("left")
        row.cell("center")
        row.cell("right")  # triggers header cell overflow on last column
        row = table.row()
        row.cell("left")
        row.cell("center")
        row.cell(
            "right", style=boldstyle
        )  # triggers header cell overflow on last column
        row = table.row()
        row.cell("A1")
        row.cell("A2")
        row.cell("A33333333")  # triggers cell overflow on last column
        row = table.row()
        row.cell("B1")
        row.cell("B2")
        row.cell("B3")

    run_comparison(pdf, "table_with_cell_overflow_font_setting", tmp_path)


def test_draw_box_borders(tmp_path):
    pdf = FPDF()
    pdf.set_font("Times", size=16)
    pdf.add_page()

    def box(x, y, borders):
        draw_box_borders(
            pdf,
            x - 10,
            y - 10,
            x + 40,
            y + 20,
            fill_color=(200, 200, 200),
            border="None",
        )
        draw_box_borders(pdf, x - 20, y - 20, x + 50, y + 30, border=borders)
        pdf.set_xy(x, y)
        pdf.cell(text=borders)

    box(40, 40, "L")
    box(140, 40, "R")

    box(40, 140, "T")
    box(140, 140, "B")

    run_comparison(pdf, "draw_box_borders", tmp_path)
