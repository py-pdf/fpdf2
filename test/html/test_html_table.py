from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal
from test.table.test_table import MULTILINE_TABLE_DATA


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def test_html_table_simple(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<table><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></tbody></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_simple.pdf", tmp_path)


def test_html_table_line_separators(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<table><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></tbody></table>""",
        table_line_separators=True,
    )
    assert_pdf_equal(pdf, HERE / "html_table_line_separators.pdf", tmp_path)


def test_html_table_th_inside_tr_issue_137(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<table border="1">
    <tr>
        <th width="40%">header1</th>
        <th width="60%">header2</th>
    </tr>
    <tr>
        <th>value1</th>
        <td>value2</td>
    </tr>
</table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_line_separators_issue_137.pdf", tmp_path)


def test_html_table_with_border(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<table border="1"><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></tbody></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_border.pdf", tmp_path)


def test_html_table_with_img(caplog, tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%">
                <img src="{}/test/image/png_images/affc57dfffa5ec448a0795738d456018.png" height="235" width="435"/>
            </td>
            <td width="50%">
                <img src="{}/test/image/image_types/insert_images_insert_png.png" height="162" width="154"/>
            </td>
        </tr>
    </table>""".replace(
            "{}", str(ROOT)
        )
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_img.pdf", tmp_path)
    assert 'Ignoring unsupported "width" / "height" set on <img> element' in caplog.text


def test_html_table_with_img_without_explicit_dimensions(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%">
                <img src="{}/test/image/png_images/affc57dfffa5ec448a0795738d456018.png"/>
            </td>
            <td width="50%">
                <img src="{}/test/image/image_types/insert_images_insert_png.png"/>
            </td>
        </tr>
    </table>""".replace(
            "{}", str(ROOT)
        )
    )
    assert_pdf_equal(
        pdf,
        HERE / "html_table_with_img_without_explicit_dimensions.pdf",
        tmp_path,
    )


def test_html_table_with_imgs_captions_and_colspan(caplog, tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<table border="1">
        <tr>
            <td colspan="2" align="center"><b>Side by side centered pictures and captions</b></td>
        </tr>
        <tr>
            <td width="50%" align="center"><img src="{}/docs/fpdf2-logo.png"/></td>
            <td width="50%" align="center"><img src="{}/docs/fpdf2-logo.png"/></td>
        </tr>
        <tr>
            <td width="50%" align="center">left caption</td>
            <td width="50%" align="center">right caption</td>
        </tr>
    </table>""".replace(
            "{}", str(ROOT)
        )
    )
    assert_pdf_equal(
        pdf,
        HERE / "html_table_with_imgs_captions_and_colspan.pdf",
        tmp_path,
    )
    assert (
        'Ignoring width="50%" specified on a <td> that is not in the first <tr>'
        in caplog.text
    )


def test_html_table_with_empty_cell_contents(tmp_path):  # issue 349
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    # Reference table cells positions:
    pdf.write_html(
        """<table><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></tbody></table>"""
    )
    # Table with empty cells:
    pdf.write_html(
        """<table><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td></td><td>3</td>
    </tr><tr>
        <td></td><td>5</td><td></td>
    </tr></tbody></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_empty_cell_contents.pdf", tmp_path)


def test_html_table_with_bgcolor(tmp_path):  # issue-512
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
    <thead>
        <tr>
            <th width="25%">Career</th>
            <th width="75%">Quote</th>
        </tr>
    </thead>
    <tbody>
        <tr bgcolor="grey"><td>Engineer</td><td>The engineer has been, and is, a maker of history.</td></tr>
        <tr bgcolor="white"><td>Developer</td><td>Logical thinking, passion and perseverance is the paint on your palette.</td></tr>
        <tr bgcolor="grey"><td>Analyst</td><td>Seeing what other people can't see gives you great vision.</td></tr>
        <tr bgcolor="white"><td><i>None of the above</i></td><td>I'm sorry. We could not find a quote for your job.</td></tr>
    </tbody>
</table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_bgcolor.pdf", tmp_path)


def test_html_table_with_only_tds(tmp_path):  # issue-740
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<table><tr>
        <td>left</td><td>center</td><td>right</td>
    </tr><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_only_tds.pdf", tmp_path)


def test_html_table_with_multi_lines_text(tmp_path):  # issue-91
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<table border="1"><thead><tr>
    <th width="30%">First name</th><th width="30%">Last name</th><th width="15%">Age</th><th width="25%">City</th>
</tr></thead><tbody><tr>
    <td>Jean Abdul William</td><td>Smith</td><td>34</td><td>San Juan</td>
</tr></tbody></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_multi_lines_text.pdf", tmp_path)


def test_html_table_with_multiline_cells_and_split_over_page(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=16)
    html = "<table><thead><tr>"
    # pylint: disable=consider-using-join
    for cell_text in MULTILINE_TABLE_DATA[0]:
        html += f"\n<th>{cell_text}</th>"
    html += "\n</tr></thead><tbody>"
    for data_row in MULTILINE_TABLE_DATA[1:-1] + MULTILINE_TABLE_DATA[1:]:
        html += "\n<tr>"
        for cell_text in data_row:
            html += f"\n<td>{cell_text}</td>"
        html += "</tr>"
    html += "\n</tbody></table>"
    pdf.write_html(html)
    assert_pdf_equal(
        pdf, HERE / "html_table_with_multiline_cells_and_split_over_page.pdf", tmp_path
    )


def test_html_table_with_width_and_align(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(24)
    pdf.add_page()
    pdf.write_html(
        """<table width=50% align=right><thead><tr>
        <th width="25%">left</th><th width="50%">center</th><th width="25%">right</th>
    </tr></thead><tbody><tr>
        <td>1</td><td>2</td><td>3</td>
    </tr><tr>
        <td>4</td><td>5</td><td>6</td>
    </tr></tbody></table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_with_width_and_align.pdf", tmp_path)


def test_html_table_invalid(caplog):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    # OK with empty tables:
    pdf.write_html("<table></table>")
    pdf.write_html("<table><tr></tr></table>")
    pdf.write_html("<table><tr><td></td></tr></table>")
    # KO if some elements are missing:
    with pytest.raises(FPDFException) as error:
        pdf.write_html("<table><td></td></table>")
    assert str(error.value) == "Invalid HTML: <td> used outside any <tr>"
    with pytest.raises(FPDFException) as error:
        pdf.write_html("<table><th></th></table>")
    assert str(error.value) == "Invalid HTML: <th> used outside any <tr>"
    with pytest.raises(FPDFException) as error:
        pdf.write_html("<tr></tr>")
    assert str(error.value) == "Invalid HTML: <tr> used outside any <table>"
    assert caplog.text == ""


def test_html_table_with_nested_tags():  # issue 845
    pdf = FPDF()
    pdf.set_font_size(24)
    pdf.add_page()
    with pytest.raises(NotImplementedError):
        pdf.write_html(
            """<table><tr>
            <th>LEFT</th>
            <th>RIGHT</th>
        </tr><tr>
            <td><font size=7>This is supported</font></td>
            <td>This <font size=20>is not</font> <b>supported</b></td>
        </tr></table>"""
        )
