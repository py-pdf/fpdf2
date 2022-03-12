from pathlib import Path

import pytest

from fpdf import FPDF, HTMLMixin
from fpdf.errors import FPDFException
from fpdf.html import px2mm
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


class MyFPDF(FPDF, HTMLMixin):
    pass


def test_html_images(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()

    initial = 10
    mm_after_image = initial + px2mm(300)
    assert round(pdf.get_x()) == 10
    assert round(pdf.get_y()) == 10
    assert round(pdf.w) == 210

    img_path = HERE.parent / "image/png_images/c636287a4d7cb1a36362f7f236564cef.png"
    pdf.write_html(
        f"<center><img src=\"{img_path}\" height='300' width='300'></center>"
    )
    # Unable to text position of the image as write html moves to a new line after
    # adding the image but it can be seen in the produce test.pdf file.
    assert round(pdf.get_x()) == 10
    assert pdf.get_y() == pytest.approx(mm_after_image, abs=0.01)

    assert_pdf_equal(pdf, HERE / "html_images.pdf", tmp_path)


def test_html_features(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html("<p><b>hello</b> world. i am <i>tired</i>.</p>")
    pdf.write_html("<p><u><b>hello</b> world. i am <i>tired</i>.</u></p>")
    pdf.write_html("<p><u><strong>hello</strong> world. i am <em>tired</em>.</u></p>")
    pdf.write_html('<p><a href="https://github.com">github</a></p>')
    pdf.write_html('<p align="right">right aligned text</p>')
    pdf.write_html("<p>i am a paragraph <br />in two parts.</p>")
    pdf.write_html('<font color="#00ff00"><p>hello in green</p></font>')
    pdf.write_html('<font size="7"><p>hello small</p></font>')
    pdf.write_html('<font face="helvetica"><p>hello helvetica</p></font>')
    pdf.write_html('<font face="times"><p>hello times</p></font>')
    pdf.write_html("<h1>h1</h1>")
    pdf.write_html("<h2>h2</h2>")
    pdf.write_html("<h3>h3</h3>")
    pdf.write_html("<h4>h4</h4>")
    pdf.write_html("<h5>h5</h5>")
    pdf.write_html("<h6>h6</h6>")
    pdf.write_html("<br />")
    pdf.write_html("<hr />")
    pdf.write_html("<br />")
    pdf.write_html("<br />")
    pdf.write_html("<pre>i am preformatted text.</pre>")
    pdf.write_html("<blockquote>hello blockquote</blockquote>")
    pdf.write_html("<ul><li>li1</li><li>another</li><li>l item</li></ul>")
    pdf.write_html("<ol><li>li1</li><li>another</li><li>l item</li></ol>")
    pdf.write_html('<table width="50"></table>')
    pdf.write_html("<img></img>")
    pdf.write_html(
        "<table>"
        "  <thead>"
        "    <tr>"
        '      <th  width="30%">ID</th>'
        '      <th  width="70%">Name</th>'
        "    </tr>"
        "  </thead>"
        "  <tbody>"
        "    <tr>"
        "      <td>1</td>"
        "      <td>Alice</td>"
        "    </tr>"
        "    <tr>"
        "      <td>2</td>"
        "      <td>Bob</td>"
        "    </tr>"
        "  </tbody>"
        "  <tfoot>"
        "    <tr>"
        '      <td width="50%">id</td>'
        '      <td width="50%">name</td>'
        "    </tr>"
        "  </tfoot>"
        "</table>"
    )
    pdf.write_html('<table width="50"></table>')
    pdf.write_html(
        '<table width="50%">'
        "  <thead>"
        "    <tr>"
        '      <th  width="30%">ID</th>'
        '      <th  width="70%">Name</th>'
        "    </tr>"
        "  </thead>"
        "  <tbody>"
        "    <tr>"
        "      <td>1</td>"
        "      <td>Alice</td>"
        "    </tr>"
        "    <tr>"
        "      <td>2</td>"
        "      <td>Bob</td>"
        "    </tr>"
        "  </tbody>"
        "  <tfoot>"
        "    <tr>"
        '      <td width="50%">id</td>'
        '      <td width="50%">name</td>'
        "    </tr>"
        "  </tfoot>"
        "</table>"
    )

    name = [
        "Alice",
        "Carol",
        "Chuck",
        "Craig",
        "Dan",
        "Erin",
        "Eve",
        "Faythe",
        "Frank",
        "Grace",
        "Heidi",
        "Ivan",
        "Judy",
        "Mallory",
        "Michael",
        "Niaj",
        "Olivia",
        "Oscar",
        "Peggy",
        "Rupert",
        "Sybil",
        "Trent",
        "Trudy",
        "Victor",
        "Walter",
        "Wendy",
    ]

    def getrow(i):
        return f"<tr><td>{i}</td><td>{name[i]}</td></tr>"

    pdf.write_html(
        (
            '<table width="50%">'
            "  <thead>"
            "    <tr>"
            '      <th  width="30%">ID</th>'
            '      <th  width="70%">Name</th>'
            "    </tr>"
            "  </thead>"
            "  <tbody>"
            "    <tr>"
            '      <td colspan="2">Alice</td>'
            "    </tr>"
        )
        + "".join(getrow(i) for i in range(26))
        + "  </tbody>"
        + "</table>"
    )

    pdf.add_page()
    img_path = HERE.parent / "image/png_images/c636287a4d7cb1a36362f7f236564cef.png"
    pdf.write_html(f"<img src=\"{img_path}\" height='300' width='300'>")

    assert_pdf_equal(pdf, HERE / "html_features.pdf", tmp_path)


def test_html_simple_table(tmp_path):
    pdf = MyFPDF()
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
    assert_pdf_equal(pdf, HERE / "html_simple_table.pdf", tmp_path)


def test_html_table_line_separators(tmp_path):
    pdf = MyFPDF()
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
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table border="1">
    <tr>
        <th width="40%">header1</th>
        <th width="60%">header2</th>
    </tr>
    <tr>
        <th width="40%">value1</th>
        <td width="60%">value2</td>
    </tr>
</table>"""
    )
    assert_pdf_equal(pdf, HERE / "html_table_line_separators_issue_137.pdf", tmp_path)


def test_html_table_with_border(tmp_path):
    pdf = MyFPDF()
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


def test_html_bold_italic_underline(tmp_path):
    pdf = MyFPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<B>bold</B>
           <I>italic</I>
           <U>underlined</U>
           <B><I><U>all at once!</U></I></B>"""
    )
    assert_pdf_equal(pdf, HERE / "html_bold_italic_underline.pdf", tmp_path)


def test_customize_ul(tmp_path):
    html = """<ul>
            <li><b>term1</b>: definition1</li>
            <li><b>term2</b>: definition2</li>
        </ul>"""
    # 1. Customizing through class attributes:
    class CustomPDF(FPDF, HTMLMixin):
        li_tag_indent = 5
        ul_bullet_char = "\x86"

    pdf = CustomPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(html)
    pdf.ln()
    # 2. Customizing through instance attributes:
    pdf.li_tag_indent = 10
    pdf.ul_bullet_char = "\x9b"
    pdf.write_html(html)
    pdf.ln()
    # 3. Customizing through optional method arguments:
    for indent, bullet in ((15, "\xac"), (20, "\xb7")):
        pdf.write_html(html, li_tag_indent=indent, ul_bullet_char=bullet)
        pdf.ln()
    assert_pdf_equal(pdf, HERE / "test_customize_ul.pdf", tmp_path)


def test_img_inside_html_table(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%">
                <img src="test/image/png_images/affc57dfffa5ec448a0795738d456018.png" height="235" width="435"/>
            </td>
            <td width="50%">
                <img src="test/image/image_types/insert_images_insert_png.png" height="162" width="154"/>
            </td>
        </tr>
    </table>"""
    )
    assert_pdf_equal(pdf, HERE / "test_img_inside_html_table.pdf", tmp_path)


def test_img_inside_html_table_without_explicit_dimensions(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%">
                <img src="test/image/png_images/affc57dfffa5ec448a0795738d456018.png"/>
            </td>
            <td width="50%">
                <img src="test/image/image_types/insert_images_insert_png.png"/>
            </td>
        </tr>
    </table>"""
    )
    assert_pdf_equal(
        pdf,
        HERE / "test_img_inside_html_table_without_explicit_dimensions.pdf",
        tmp_path,
    )


def test_img_inside_html_table_centered(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%"><center>
                <img src="test/image/png_images/affc57dfffa5ec448a0795738d456018.png" height="235" width="435"/>
            </center></td>
            <td width="50%"><center>
                <img src="test/image/image_types/insert_images_insert_png.png" height="162" width="154"/>
            </center></td>
        </tr>
    </table>"""
    )
    assert_pdf_equal(pdf, HERE / "test_img_inside_html_table_centered.pdf", tmp_path)


def test_img_inside_html_table_centered_with_align(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table>
        <tr>
            <td width="50%" align="center">
                <img src="test/image/png_images/affc57dfffa5ec448a0795738d456018.png" height="235" width="435"/>
            </td>
            <td width="50%" align="center">
                <img src="test/image/image_types/insert_images_insert_png.png" height="162" width="154"/>
            </td>
        </tr>
    </table>"""
    )
    assert_pdf_equal(
        pdf, HERE / "test_img_inside_html_table_centered_with_align.pdf", tmp_path
    )


def test_img_inside_html_table_centered_with_caption(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<table border="1">
        <tr>
            <td colspan="2" align="center"><b>Side by side centered pictures and captions</b></td>
        </tr>
        <tr>
            <td width="50%" align="center"><img src="docs/fpdf2-logo.png" height="200" width="200"/></td>
            <td width="50%" align="center"><img src="docs/fpdf2-logo.png" height="200" width="200"/></td>
        </tr>
        <tr>
            <td width="50%" align="center">left caption</td>
            <td width="50%" align="center">right caption</td>
        </tr>
    </table>"""
    )
    assert_pdf_equal(
        pdf, HERE / "test_img_inside_html_table_centered_with_caption.pdf", tmp_path
    )


def test_html_table_with_empty_cell_contents(tmp_path):  # issue 349
    pdf = MyFPDF()
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


def test_html_justify_paragraph(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        '<p align="justify">'
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        " Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
        " Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."
        " Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        "</p>"
    )
    assert_pdf_equal(pdf, HERE / "html_justify_paragraph.pdf", tmp_path)


def test_issue_156(tmp_path):
    pdf = MyFPDF()
    pdf.add_font("Roboto", style="B", fname="test/fonts/Roboto-Bold.ttf")
    pdf.set_font("Roboto", style="B")
    pdf.add_page()
    with pytest.raises(FPDFException) as error:
        pdf.write_html("Regular text<br><b>Bold text</b>")
    assert (
        str(error.value)
        == "Undefined font: roboto - Use built-in fonts or FPDF.add_font() beforehand"
    )
    pdf.add_font("Roboto", fname="test/fonts/Roboto-Regular.ttf")
    pdf.write_html("Regular text<br><b>Bold text</b>")
    assert_pdf_equal(pdf, HERE / "issue_156.pdf", tmp_path)


def test_html_font_color_name(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        '<font color="crimson"><p>hello in crimson</p></font>'
        '<font color="#f60"><p>hello in orange</p></font>'
        '<font color="LIGHTBLUE"><p><b>bold hello in light blue</b></p></font>'
        '<font color="royalBlue"><p>hello in royal blue</p></font>'
        '<font color="#000"><p>hello in black</p></font>'
        '<font color="beige"><p><i>italic hello in beige</i></p></font>'
    )
    assert_pdf_equal(pdf, HERE / "html_font_color_name.pdf", tmp_path)


def test_html_heading_hebrew(tmp_path):
    pdf = MyFPDF()
    pdf.add_font("DejaVuSans", fname=HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVuSans")
    pdf.add_page()
    pdf.write_html("<h1>Hebrew: שלום עולם</h1>")
    assert_pdf_equal(pdf, HERE / "html_heading_hebrew.pdf", tmp_path)


def test_html_headings_line_height(tmp_path):  # issue-223
    pdf = MyFPDF()
    pdf.add_page()
    long_title = "The Quick Brown Fox Jumped Over The Lazy Dog "
    pdf.write_html(
        f"""
    <h1>H1   {long_title*2}</h1>
    <h2>H2   {long_title*2}</h2>
    <h3>H3   {long_title*2}</h3>
    <h4>H4   {long_title*3}</h4>
    <h5>H5   {long_title*3}</h5>
    <h6>H6   {long_title*4}</h6>
    <p>P   {long_title*5}<p>"""
    )
    assert_pdf_equal(pdf, HERE / "html_headings_line_height.pdf", tmp_path)


def test_html_custom_heading_sizes(tmp_path):  # issue-223
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<h1>This is a H1</h1>
           <h2>This is a H2</h2>
           <h3>This is a H3</h3>
           <h4>This is a H4</h4>
           <h5>This is a H5</h5>
           <h6>This is a H6</h6>""",
        heading_sizes=dict(h1=6, h2=12, h3=18, h4=24, h5=30, h6=36),
    )
    assert_pdf_equal(pdf, HERE / "html_custom_heading_sizes.pdf", tmp_path)
