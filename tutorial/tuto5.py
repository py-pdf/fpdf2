import csv
from fpdf import FPDF
from fpdf.fonts import FontStyle


with open("countries.txt", encoding="utf8") as csv_file:
    data = list(csv.reader(csv_file, delimiter=","))

pdf = FPDF()
pdf.set_font("helvetica", size=14)

# Basic table:
pdf.add_page()
with pdf.table() as table:
    for data_row in data:
        with table.row() as row:
            for datum in data_row:
                row.cell(datum)

# Styled table:
pdf.add_page()
pdf.set_draw_color(255, 0, 0)
pdf.set_line_width(0.3)
with pdf.table() as table:
    table.borders_layout = "NO_HORIZONTAL_LINES"
    table.cell_fill_color = (224, 235, 255)
    table.cell_fill_logic = lambda i, j: i % 2
    table.col_widths = (42, 39, 35, 42)
    table.headings_style = FontStyle(
        emphasis="BOLD", color=255, fill_color=(255, 100, 0)
    )
    table.line_height = 6
    table.text_align = ("LEFT", "CENTER", "RIGHT", "RIGHT")
    table.width = 160
    for data_row in data:
        with table.row() as row:
            for datum in data_row:
                row.cell(datum)

pdf.output("tuto5.pdf")
