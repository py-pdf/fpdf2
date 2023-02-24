from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.drawing import DeviceRGB
from fpdf.fonts import FontStyle
from test.conftest import assert_pdf_equal, LOREM_IPSUM


HERE = Path(__file__).resolve().parent

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
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


def test_table_simple(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_simple.pdf", tmp_path)


def test_table_with_fixed_col_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.col_widths = pdf.epw / 5
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_fixed_col_width.pdf", tmp_path)


def test_table_with_varying_col_widths(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.col_widths = (30, 30, 10, 30)
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_varying_col_widths.pdf", tmp_path)


def test_table_with_invalid_col_widths():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pytest.raises(ValueError):
        with pdf.table() as table:
            table.col_widths = (20, 30, 50)
            for data_row in TABLE_DATA:
                with table.row() as row:
                    for datum in data_row:
                        row.cell(datum)


def test_table_with_fixed_row_height(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.line_height = 2.5 * pdf.font_size
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_fixed_row_height.pdf", tmp_path)


def test_table_with_multiline_cells(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for data_row in MULTILINE_TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_multiline_cells.pdf", tmp_path)


def test_table_with_multiline_cells_and_fixed_row_height(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.line_height = 2.5 * pdf.font_size
        for data_row in MULTILINE_TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(
        pdf, HERE / "table_with_multiline_cells_and_fixed_row_height.pdf", tmp_path
    )


def test_table_with_fixed_width(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.width = 150
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_fixed_width.pdf", tmp_path)


def test_table_without_headings(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.first_row_as_headings = False
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_without_headings.pdf", tmp_path)


def test_table_with_multiline_cells_and_without_headings(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.first_row_as_headings = False
        for data_row in MULTILINE_TABLE_DATA + MULTILINE_TABLE_DATA[1:]:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(
        pdf, HERE / "table_with_multiline_cells_and_without_headings.pdf", tmp_path
    )


def test_table_with_headings_styled(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        blue = DeviceRGB(r=0, g=0, b=1)
        grey = 128
        table.headings_style = FontStyle(
            emphasis="ITALICS", color=blue, fill_color=grey
        )
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_headings_styled.pdf", tmp_path)


def test_table_with_multiline_cells_and_split_over_3_pages(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        for data_row in MULTILINE_TABLE_DATA + MULTILINE_TABLE_DATA[1:]:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(
        pdf, HERE / "table_with_multiline_cells_and_split_over_3_pages.pdf", tmp_path
    )


def test_table_with_cell_fill(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.cell_fill_color = 200  # grey
        table.cell_fill_logic = lambda i, j: i % 2
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_cell_fill.pdf", tmp_path)


def test_table_with_cell_fill2(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.cell_fill_color = (173, 216, 230)  # light blue
        table.cell_fill_logic = lambda i, j: j % 2
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_cell_fill2.pdf", tmp_path)


def test_table_with_internal_layout(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.borders_layout = "INTERNAL"
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_internal_layout.pdf", tmp_path)


def test_table_with_minimal_layout(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.set_draw_color(100)  # dark grey
    pdf.set_line_width(1)
    with pdf.table() as table:
        table.borders_layout = "MINIMAL"
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_minimal_layout.pdf", tmp_path)


def test_table_with_single_top_line_layout(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    pdf.set_draw_color(50)  # very dark grey
    pdf.set_line_width(0.5)
    with pdf.table() as table:
        table.borders_layout = "SINGLE_TOP_LINE"
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_with_single_top_line_layout.pdf", tmp_path)


def test_table_align(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    with pdf.table() as table:
        table.align = "CENTER"
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    pdf.ln()
    with pdf.table() as table:
        table.align = ("CENTER", "CENTER", "RIGHT", "LEFT")
        for data_row in TABLE_DATA:
            with table.row() as row:
                for datum in data_row:
                    row.cell(datum)
    assert_pdf_equal(pdf, HERE / "table_align.pdf", tmp_path)
