from fpdf import FPDF
import pandas as pd

DF = pd.DataFrame(
    {
        "First name": ["Jules", "Mary", "Carlson", "Lucas"],
        "Last name": ["Smith", "Ramos", "Banks", "Cimon"],
        "Age": [34, 45, 19, 31],
        "City": ["San Juan", "Orlando", "Los Angeles", "Saint-Mahturin-sur-Loire"],
    }
    # Convert all data inside dataframe into string type:
).applymap(str)

COLUMNS = [list(DF)]  # Get list of dataframe columns
ROWS = DF.values.tolist()  # Get list of dataframe rows
DATA = COLUMNS + ROWS  # Combine columns and rows in one list

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=10)
with pdf.table(
    borders_layout="MINIMAL",
    cell_fill_color=200,  # grey
    cell_fill_mode="ROWS",
    line_height=pdf.font_size * 2.5,
    text_align="CENTER",
    width=160,
) as table:
    for data_row in DATA:
        row = table.row()
        for datum in data_row:
            row.cell(datum)
pdf.output("table_from_pandas.pdf")
