from pathlib import Path

from fpdf import FPDF, FontFace
from fpdf.enums import TableSpan

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
IMG_DIR = HERE.parent / "image"


def test_table_with_rowspan(tmp_path):
    # Verify that tables with overlapping rowspans are calculated correctly
    pdf = FPDF()
    pdf.set_font("Times", size=24)

    # Test direct cell interface
    pdf.add_page()
    pdf.write(text="Defined with attributes\n\n")
    with pdf.table(text_align="CENTER", first_row_as_headings=False) as table:
        row = table.row()
        row.cell("A1", rowspan=3)
        row.cell("B1")
        row.cell("C1")
        row.cell("D1", rowspan=3)
        row = table.row()
        row.cell("B2", rowspan=4)
        row.cell("C2", rowspan=2)
        row = table.row()  # empty row fully spanned by previous rows
        row = table.row()
        row.cell("A3")
        row.cell("C3", rowspan=2)
        row.cell("D3", rowspan=2)
        row = table.row()
        row.cell("A4")

    # Test placeholder interface
    TABLE_DATA = [
        ["A1", "B1", "C1", "D1"],
        [TableSpan.ROW, "B2", "C2", TableSpan.ROW],
        [TableSpan.ROW, TableSpan.ROW, TableSpan.ROW, TableSpan.ROW],
        ["A3", TableSpan.ROW, "C3", "D3"],
        ["A4", TableSpan.ROW, TableSpan.ROW, TableSpan.ROW],
    ]
    pdf.add_page()
    pdf.write(text="Defined with items\n\n")
    with pdf.table(TABLE_DATA, text_align="CENTER", first_row_as_headings=False):
        pass

    # Test HTML interface
    pdf.add_page()
    pdf.write(text="Defined in HTML\n\n")
    pdf.write_html(
        """
        <table border=1>
        <tr align=center><td rowspan=3>A1</td><td>B1</td><td>C1</td><td rowspan=3>D1</td></tr>
        <tr align=center><td rowspan=4>B2</td><td rowspan=2>C2</td></tr>
        <tr></tr>
        <tr align=center><td>A3</td><td rowspan=2>C3</td><td rowspan=2>D3</td></tr>
        <tr align=center><td>A4</td></tr>
        </table>
    """,
        table_line_separators=True,
    )

    assert_pdf_equal(pdf, HERE / "table_with_rowspan.pdf", tmp_path)


def test_table_with_rowspan_and_colspan(tmp_path):
    # Verify that tables with both rowspans and colspans are calculated correctly
    #
    pdf = FPDF()
    pdf.set_font("Helvetica")
    options = dict(text_align="CENTER", gutter_width=5, gutter_height=5)
    red_fill = FontFace(emphasis="BIU", color=255, fill_color=(255, 0, 0))
    blue_fill = FontFace(emphasis="BOLD", color=255, fill_color=(0, 0, 255))

    # Test direct cell interface
    pdf.add_page()
    pdf.write(text="Defined with attributes\n\n")
    with pdf.table(**options) as table:
        row = table.row(["A", "B", "C", "D"])
        row = table.row()
        row.cell("A1", colspan=2, rowspan=3, style=red_fill)
        row.cell("C1", colspan=2, style=blue_fill)
        row = table.row()
        row.cell("C2", colspan=2, rowspan=2, style=red_fill)
        row = table.row()  # all columns of this row are spanned by previous rows
        row = table.row()
        row.cell("A4", colspan=4, style=blue_fill)
        row = table.row()
        row.cell("A5", colspan=2, style=blue_fill)
        row.cell("C5")
        row.cell("D5")
        row = table.row()
        row.cell("A6")
        row.cell("B6", colspan=2, rowspan=2, style=red_fill)
        row.cell("D6", rowspan=2, style=blue_fill)
        row = table.row()
        row.cell("A7")

    # Test placeholder interface
    TABLE_DATA = [
        ["A", "B", "C", "D"],
        ["A1", TableSpan.COL, "C1", TableSpan.COL],
        [TableSpan.ROW, TableSpan.ROW, "C2", TableSpan.COL],
        [TableSpan.ROW, TableSpan.ROW, TableSpan.ROW, TableSpan.ROW],
        ["A4", TableSpan.COL, TableSpan.COL, TableSpan.COL],
        ["A5", TableSpan.COL, "C5", "D5"],
        ["A6", "B6", TableSpan.COL, "D6"],
        ["A7", TableSpan.ROW, TableSpan.ROW, TableSpan.ROW],
    ]
    pdf.add_page()
    pdf.write(text="Defined with items\n\n")
    with pdf.table(TABLE_DATA, **options):
        pass

    # Test HTML interface
    # Not all options are available from HTML, but it should be close enough to verify
    HTML_DATA = """
        <table border=1 cellspacing=5 cellpadding=3>
        <tr align=center><th>A</th><th>B</th><th>C</th><th>D</th></tr>
        <tr align=center><td rowspan=3 colspan=2>A1</td><td colspan=2>C1</td></tr>
        <tr align=center><td rowspan=2 colspan=2>C2</td></tr>
        <tr></tr>
        <tr align=center><td colspan=4>A4</td></tr>
        <tr align=center><td colspan=2>A5</td><td>C5</td><td>D5</td></tr>
        <tr align=center><td>A6</td><td colspan=2 rowspan=2>B6</td><td rowspan=2>D6</td></tr>
        <tr align=center><td>A7</td></tr>
        </table>
    """
    pdf.add_page()
    pdf.write(text="Defined in HTML\n\n")
    pdf.write_html(HTML_DATA, table_line_separators=True)

    assert_pdf_equal(pdf, HERE / "table_with_rowspan_and_colspan.pdf", tmp_path)


def test_table_with_rowspan_and_pgbreak(tmp_path):
    # Verify that the rowspans interact correctly with pagebreaks
    pdf = FPDF()
    pdf.set_font("Helvetica")
    line_opts = dict(line_width=1, draw_color=(0, 255, 0))
    table_opts = dict(
        text_align="CENTER",
        headings_style=FontFace(emphasis="BOLD", fill_color=200),
        num_heading_rows=3,
    )

    # Interpreting span definitions from a string is application-dependent
    # Separation of placeholder strings from valid strings must be done in advance
    # Here is one demonstration with a markdown-style table extension
    TABLE_STRING = """
Location|<|Division A|<|<|<|Division B|<
^|^|Partition 1|<|Partition 2|<|^|^
X|Y|A|B|A|B|A|B
Internal|East|1-1|1-2|1-3|1-4|1-5|1-6
^|Central|^|2-2|^|2-4|^|2-6
^|West|3-1|^|3-3|^|3-5|^
External|East|4-1|4-2|4-3|4-4|4-5|<
^|Central|5-1|5-2|5-3|<|5-5|5-6
^|West|6-1|<|6-3|6-4|6-5|6-6
    """
    SPAN_SUB = {"<": TableSpan.COL, "^": TableSpan.ROW}
    TABLE_DATA = [
        [SPAN_SUB.get(datum, datum) for datum in row.split("|")]
        for row in TABLE_STRING.strip().splitlines()
    ]

    pdf.add_page()
    y0 = pdf.h - pdf.b_margin
    with pdf.local_context(**line_opts):
        pdf.line(0, y0, pdf.w, y0)

    # simple table
    # with pdf.table(TABLE_DATA, **table_opts):
    with pdf.table(TABLE_DATA, **table_opts):
        pass

    # test breaking within a rowspan of the data block
    # -- verify break occurs before the offending rowspan
    # -- verify header reproduction
    pdf.set_y(pdf.h - 85)
    with pdf.local_context(**line_opts):
        pdf.line(0, pdf.y, pdf.w, pdf.y)
    with pdf.table(TABLE_DATA, **table_opts):
        pass

    # test breaking within the header
    # allow room for two rows of the table, but not three
    pdf.set_y(y0 - 20)
    with pdf.local_context(**line_opts):
        pdf.line(0, y0, pdf.w, y0)
        pdf.line(0, pdf.y, pdf.w, pdf.y)
    with pdf.table(TABLE_DATA, **table_opts):
        pass

    # test breaking inside a rowspan in the header
    # allow room for one row of the table, but not two
    pdf.set_y(y0 - 15)
    with pdf.local_context(**line_opts):
        pdf.line(0, y0, pdf.w, y0)
        pdf.line(0, pdf.y, pdf.w, pdf.y)
    with pdf.table(TABLE_DATA, **table_opts):
        pass

    # test breaking when there's nowhere good to do it
    # the continually overlapping rowspans mean the whole table must be kept together
    pdf.set_y(pdf.h * 2 / 3)
    with pdf.local_context(**line_opts):
        pdf.line(0, y0, pdf.w, y0)
        pdf.line(0, pdf.y, pdf.w, pdf.y)
    with pdf.table(text_align="CENTER") as table:
        table.row(["H1", "H2", "H3", "H4"])
        for i in range(15):
            row = table.row()
            for j, c in enumerate("ABCD"):
                ij = (5 + i - j) % 5
                rowspan = 3 if ij == 0 else 1
                if i <= j or ij == 0 or ij > 2:
                    row.cell(f"{c}{i}", rowspan=rowspan)
        table.row(["A15", "B15", "C15"])

    assert_pdf_equal(pdf, HERE / "table_with_rowspan_and_pgbreak.pdf", tmp_path)


def test_table_with_rowspan_images(tmp_path):
    # Verify that the rowspans interact correctly with pagebreaks
    pdf = FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    with pdf.table(text_align="CENTER", col_widths=(8, 10, 6)) as table:
        table.row(["Image", "Text", "Image"])

        row = table.row()
        row.cell(
            img=IMG_DIR / "png_images/ba2b2b6e72ca0e4683bb640e2d5572f8.png", rowspan=3
        )
        row.cell("One line of text")
        row.cell(img=IMG_DIR / "image_types/insert_images_insert_jpg.jpg", rowspan=2)

        table.row().cell("Two lines\nof text")

        row = table.row()
        # row.cell("Three\nlines\nof text")
        row.cell("One line of text")
        row.cell(img=IMG_DIR / "image_types/insert_images_insert_png.png", rowspan=2)

        row = table.row()
        row.cell(img=IMG_DIR / "image_types/circle.gif")
        row.cell("Two lines\nof text")

        row = table.row()
        row.cell(img=IMG_DIR / "image_types/insert_images_insert_jpg.jpg", rowspan=2)
        row.cell("One line of text")
        row.cell(img=IMG_DIR / "image_types/pythonknight.png", rowspan=2)

        row = table.row()
        row.cell("Four\nlines\nof\ntext")

    assert_pdf_equal(pdf, HERE / "table_with_rowspan_images.pdf", tmp_path)
