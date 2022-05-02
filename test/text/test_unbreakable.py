from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent

TABLE_DATA = (
    ("First name", "Last name", "Age", "City"),
    ("Jules", "Smith", "34", "San Juan"),
    ("Mary", "Ramos", "45", "Orlando"),
    ("Carlson", "Banks", "19", "Los Angeles"),
    ("Lucas", "Cimon", "31", "Angers"),
)


def test_multi_cell_table_unbreakable(tmp_path):  # issue 111
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    line_height = pdf.font_size * 2
    col_width = pdf.epw / 4  # distribute content evenly
    for i in range(5):  # repeat table 5 times
        with pdf.unbreakable() as pdf:
            for row in TABLE_DATA:
                for datum in row:
                    pdf.multi_cell(
                        col_width,
                        line_height,
                        f"{datum} ({i})",
                        border=1,
                        new_x="RIGHT",
                        new_y="TOP",
                    )
                pdf.ln(line_height)
        pdf.ln(line_height * 2)
    assert_pdf_equal(pdf, HERE / "multi_cell_table_unbreakable.pdf", tmp_path)


def test_multi_cell_table_unbreakable2(tmp_path):  # issue 120 - 2nd snippet
    table = {
        "A": "test_lin_o_00000_001",
        "B": "3",
        "C": "4",
        "D": "test_lin_o_00000",
        "E": "7",
        "F": "test_lin_o_00000",
        "G": "test_lin",
        "H": "test_lin",
    }
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20)
    pdf.set_font("Times", "B", size=7)
    line_height = pdf.font_size * 3
    col_width = pdf.epw / 8
    for header in table:
        pdf.multi_cell(
            col_width,
            line_height,
            header,
            border=1,
            new_x="RIGHT",
            new_y="TOP",
            max_line_height=pdf.font_size,
            align="C",
        )
    pdf.ln(line_height)
    pdf.set_font(style="")
    line_height = pdf.font_size * 10
    col_width = pdf.epw / 8
    for _ in range(11):
        with pdf.unbreakable():
            for cell in table.values():
                pdf.multi_cell(
                    col_width,
                    line_height,
                    cell,
                    border=1,
                    new_x="RIGHT",
                    new_y="TOP",
                    max_line_height=pdf.font_size,
                    align="C",
                )
        pdf.ln(line_height)
    assert_pdf_equal(pdf, HERE / "multi_cell_table_unbreakable2.pdf", tmp_path)


def test_multi_cell_table_unbreakable_with_split_only(tmp_path):  # issue 359
    pdf = fpdf.FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(True, 20)
    pdf.set_font("Helvetica", "", 10)
    pdf.add_page()

    data = (
        ("First name", "Last name", "Age", "City"),
        ("Jules", "Smith", "34", "San Juan"),
        ("Mary", "Ramos", "45", "Orlando"),
        ("Carlson", "Banks", "19", "Los Angeles"),
        ("Lucas", "Cimon", "31", "Angers"),
        ("Jules", "Smith", "34", "San Juan"),
        ("Mary", "Ramos", "45", "Orlando"),
        ("Carlson", "Banks", "19", "Los Angeles"),
        ("Lucas", "Cimon", "31", "Angers"),
        ("Jules", "Smith", "34", "San Juan"),
        ("Mary", "Ramos", "45", "Orlando"),
        ("Carlson", "Banks", "19", "Los Angeles"),
        ("Lucas", "Cimon", "31", "Angers"),
    )
    l_height = pdf.font_size * 1.2
    cell_width = pdf.epw / 4
    no_of_lines_list = []

    for row in data:
        max_no_of_lines_in_cell = 1
        for cell in row:
            result = pdf.multi_cell(
                cell_width,
                l_height,
                cell,
                border=1,
                align="L",
                new_x="RIGHT",
                new_y="TOP",
                max_line_height=l_height,
                split_only=True,
            )
            no_of_lines_in_cell = len(result)
            if no_of_lines_in_cell > max_no_of_lines_in_cell:
                max_no_of_lines_in_cell = no_of_lines_in_cell
        no_of_lines_list.append(max_no_of_lines_in_cell)

    for j, row in enumerate(data):
        cell_height = no_of_lines_list[j] * l_height
        for cell in row:
            if j == 0:
                pdf.multi_cell(
                    cell_width,
                    cell_height,
                    "**" + cell + "**",
                    border=1,
                    fill=False,
                    align="L",
                    new_x="RIGHT",
                    new_y="TOP",
                    max_line_height=l_height,
                    markdown=False,
                )
            else:
                pdf.multi_cell(
                    cell_width,
                    cell_height,
                    cell,
                    border=1,
                    align="L",
                    new_x="RIGHT",
                    new_y="TOP",
                    max_line_height=l_height,
                )
        pdf.ln(cell_height)

    pdf.ln()

    with pdf.unbreakable() as pdf:
        for _ in range(4):
            for row in data:
                max_no_of_lines_in_cell = 1
                for cell in row:
                    result = pdf.multi_cell(
                        cell_width,
                        l_height,
                        cell,
                        border=1,
                        align="L",
                        new_x="RIGHT",
                        new_y="TOP",
                        max_line_height=l_height,
                        split_only=True,
                    )
                    no_of_lines_in_cell = len(result)
                    if no_of_lines_in_cell > max_no_of_lines_in_cell:
                        max_no_of_lines_in_cell = no_of_lines_in_cell
                no_of_lines_list.append(max_no_of_lines_in_cell)

            for j, row in enumerate(data):
                cell_height = no_of_lines_list[j] * l_height
                for cell in row:
                    if j == 0:
                        pdf.multi_cell(
                            cell_width,
                            cell_height,
                            "**" + cell + "**",
                            border=1,
                            fill=False,
                            align="L",
                            new_x="RIGHT",
                            new_y="TOP",
                            max_line_height=l_height,
                            markdown=False,
                        )
                    else:
                        pdf.multi_cell(
                            cell_width,
                            cell_height,
                            cell,
                            border=1,
                            align="L",
                            new_x="RIGHT",
                            new_y="TOP",
                            max_line_height=l_height,
                        )
                pdf.ln(cell_height)

    assert_pdf_equal(
        pdf, HERE / "multi_cell_table_unbreakable_with_split_only.pdf", tmp_path
    )
