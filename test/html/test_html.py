from pathlib import Path

import pytest

import fpdf
from fpdf.html import px2mm
from test.utilities import assert_pdf_equal


HERE = Path(__file__).resolve().parent


class MyFPDF(fpdf.FPDF, fpdf.HTMLMixin):
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
        + "".join([getrow(i) for i in range(26)])
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
