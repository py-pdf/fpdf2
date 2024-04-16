from pathlib import Path

import pytest

from fpdf import FPDF, FontFace, HTMLMixin, TitleStyle
from fpdf.drawing import DeviceRGB
from fpdf.html import color_as_decimal
from fpdf.errors import FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM


HERE = Path(__file__).resolve().parent


def test_html_images(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    initial = 10
    mm_after_image = initial + 300 / pdf.k
    assert round(pdf.get_x()) == 10
    assert round(pdf.get_y()) == 10
    assert round(pdf.w) == 210

    img_path = HERE.parent / "image/png_images/c636287a4d7cb1a36362f7f236564cef.png"
    pdf.write_html(
        f"<center><img src=\"{img_path}\" height='300' width='300'></center>"
    )
    # Unable to text position of the image as write html moves to a new line after
    # adding the image but it can be seen in the resulting html_images.pdf file.
    assert round(pdf.get_x()) == 10
    assert pdf.get_y() == pytest.approx(mm_after_image, abs=0.01)

    assert_pdf_equal(pdf, HERE / "html_images.pdf", tmp_path)


def test_html_features(tmp_path):
    pdf = FPDF()
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
    pdf.write_html("<dl><dt>description title</dt><dd>description details</dd></dl>")
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
        "      <td>id</td>"
        "      <td>name</td>"
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
        "      <td>id</td>"
        "      <td>name</td>"
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
            '      <td colspan="2" align="center">Alice</td>'
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


def test_html_bold_italic_underline(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<B>bold</B>
           <I>italic</I>
           <U>underlined</U>
           <B><I><U>all at once!</U></I></B>"""
    )
    assert_pdf_equal(pdf, HERE / "html_bold_italic_underline.pdf", tmp_path)


def test_html_customize_ul(tmp_path):
    html = """<ul>
        <li><b>term1</b>: definition1</li>
        <li><b>term2</b>: definition2</li>
    </ul>"""

    # 1. Customizing through class attributes:
    class CustomPDF(FPDF):
        li_tag_indent = 5
        ul_bullet_char = "\x86"

    pdf = CustomPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    with pytest.warns(DeprecationWarning):  # li_tag_indent
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
    assert_pdf_equal(pdf, HERE / "html_customize_ul.pdf", tmp_path)


def test_html_ol_start_and_type(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        """<ol start="2" type="i">
            <li>item</li>
            <li>item</li>
            <li>item</li>
        </ol>"""
    )
    assert_pdf_equal(pdf, HERE / "html_ol_start_and_type.pdf", tmp_path)


def test_html_ul_type(tmp_path):
    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(
        text="""
        <ul type="circle">
          <li>a list item</li>
        </ul>
        <ul type="disc">
          <li>another list item</li>
        </ul>
    """
    )
    pdf.ln()
    pdf.add_font(fname=HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVuSans")
    pdf.write_html(
        """
        <ul type="■">
          <li>a list item</li>
          <li>another list item</li>
        </ul>
    """
    )
    assert_pdf_equal(pdf, HERE / "html_ul_type.pdf", tmp_path)


def test_html_li_prefix_color(tmp_path):
    html = """<ul>
        <li>item1</li>
        <li>item2</li>
        <li>item3</li>
    </ul>"""

    pdf = FPDF()
    pdf.set_font_size(30)
    pdf.add_page()
    pdf.write_html(html, li_prefix_color=0)  # black
    pdf.ln()
    pdf.write_html(html, li_prefix_color="green")
    pdf.ln()
    pdf.write_html(html, li_prefix_color=DeviceRGB(r=0.5, g=1, b=0))
    pdf.ln()
    assert_pdf_equal(pdf, HERE / "html_li_prefix_color.pdf", tmp_path)


def test_html_align_paragraph(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(50, 20)
    pdf.write_html(
        f"""
        No align given, default left:
        <p>{LOREM_IPSUM[:200]}"</p>
        align=justify:
        <p align="justify">{LOREM_IPSUM[:200]}"</p>
        align=right:
        <p align="right">{LOREM_IPSUM[200:400]}"</p>
        align=left:
        <p align="left">{LOREM_IPSUM[400:600]}"</p>
        align=center:
        <p align="center">{LOREM_IPSUM[600:800]}"</p>
        <!-- ignore invalid align -->
        align=invalid, ignore and default left:
        <p align="invalid">{LOREM_IPSUM[800:1000]}"</p>
        """
    )
    assert_pdf_equal(pdf, HERE / "html_align_paragraph.pdf", tmp_path)


def test_issue_156(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", style="B", fname=HERE / "../fonts/Roboto-Bold.ttf")
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
    pdf = FPDF()
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
    pdf = FPDF()
    pdf.add_font(fname=HERE / "../fonts/DejaVuSans.ttf")
    pdf.set_font("DejaVuSans")
    pdf.add_page()
    pdf.write_html("<h1>Hebrew: שלום עולם</h1>")
    assert_pdf_equal(pdf, HERE / "html_heading_hebrew.pdf", tmp_path)


def test_html_headings_line_height(tmp_path):  # issue-223
    pdf = FPDF()
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
    <p>P   {long_title*5}</p>"""
    )
    assert_pdf_equal(pdf, HERE / "html_headings_line_height.pdf", tmp_path)


def test_html_custom_heading_sizes(tmp_path):  # issue-223
    pdf = FPDF()
    pdf.add_page()
    with pytest.warns(DeprecationWarning):
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


def test_html_superscript(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        "<h1>Superscript/Subscript test</h1>"
        "2<sup>56</sup> more line text<sub>(idx)</sub>"
    )
    assert_pdf_equal(pdf, HERE / "html_superscript.pdf", tmp_path)


def test_html_description(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """
           <dt>description title</dt>
           <dd>description details</dd>
            <dl>
                <dt>description title</dt>
                <dd>description details</dd>
            </dl>
        """
    )
    assert_pdf_equal(pdf, HERE / "html_description.pdf", tmp_path)


def test_html_HTMLMixin_deprecation_warning(tmp_path):
    class PDF(FPDF, HTMLMixin):
        pass

    msg = (
        "The HTMLMixin class is deprecated since v2.6.0. "
        "Simply use the FPDF class as a replacement."
    )

    with pytest.warns(DeprecationWarning, match=msg) as record:
        pdf = PDF()
        pdf.add_page()
        pdf.write_html(
            """
           <dt>description title</dt>
           <dd>description details</dd>
            <dl>
                <dt>description title</dt>
                <dd>description details</dd>
            </dl>
        """
        )
        assert_pdf_equal(pdf, HERE / "html_description.pdf", tmp_path)

    assert len(record) == 1
    assert record[0].filename == __file__


def test_html_whitespace_handling(tmp_path):  # Issue 547
    """Testing whitespace handling for write_html()."""
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """
<body>
<h1>Issue 547 Test</h1>
<p>
<b>Testing   </b> paragraph blocks
        that <i>span</i> <b>multiple lines</b>.
    Testing tabs       and    spaces<br>
    and break tags.<br>
</p>
<code>Testing code blocks with tabs      and    spaces.</code><br>
<pre>
Testing pre blocks
that span multiple lines
and have tabs    and    spaces.
</pre>

<pre><code>
Testing pre-code blocks
that span multiple lines
and have tabs    and    spaces.
</code></pre>

<p>Testing unicode nbsp \u00a0\u00a0\u00a0\u00a0,
and html nbsp &nbsp;&nbsp;&nbsp;&nbsp;.<br>
    \u00a0&nbsp;&nbsp;Testing leading nbsp
</p>
</body>
"""
    )
    assert_pdf_equal(pdf, HERE / "html_whitespace_handling.pdf", tmp_path)


def test_html_custom_line_height(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<p line-height=3>
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text</p>
<p line-height="2">
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text-</p>
<p line-height="x"><!-- invalid line-height ignored, default value of 1 will be used -->
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text-
text-text-text-text-text-text-text-text-text-text-</p>
"""
    )
    assert_pdf_equal(pdf, HERE / "html_custom_line_height.pdf", tmp_path)


def test_html_img_not_overlapping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<img src="test/image/png_images/affc57dfffa5ec448a0795738d456018.png"/>
<p>text</p>
"""
    )
    assert_pdf_equal(
        pdf,
        HERE / "html_img_not_overlapping.pdf",
        tmp_path,
    )


def test_warn_on_tags_not_matching(caplog):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html("<p>")
    assert "Missing HTML end tag for <p>" in caplog.text
    pdf.write_html("</p>")
    assert " Unexpected HTML end tag </p>" in caplog.text
    pdf.write_html("<p></a>")
    assert " Unexpected HTML end tag </a>" in caplog.text


def test_html_unorthodox_headings_hierarchy(tmp_path):  # issue 631
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """<h1>H1</h1>
           <h5>H5</h5>"""
    )
    assert_pdf_equal(pdf, HERE / "html_unorthodox_headings_hierarchy.pdf", tmp_path)


def test_html_custom_pre_code_font(tmp_path):  # issue 770
    pdf = FPDF()
    pdf.add_font(fname=HERE / "../fonts/DejaVuSansMono.ttf")
    pdf.add_page()
    with pytest.warns(DeprecationWarning):
        pdf.write_html("<code> Cześć! </code>", pre_code_font="DejaVuSansMono")
    assert_pdf_equal(pdf, HERE / "html_custom_pre_code_font.pdf", tmp_path)


def test_html_preserve_initial_text_color(tmp_path):  # issue 846
    pdf = FPDF()
    pdf.add_page()
    pdf.set_text_color(200, 50, 50)
    pdf.set_font(family="Helvetica", size=13)
    pdf.write_html("one <font size=8>two</font> three")
    assert_pdf_equal(pdf, HERE / "html_preserve_initial_text_color.pdf", tmp_path)


def test_html_heading_color_attribute(tmp_path):  # discussion 880
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """
      <h1>Title</h1>
      Content
      <h2 color="#00ff00">Subtitle in green</h2>
      Content
    """
    )
    assert_pdf_equal(pdf, HERE / "html_heading_color_attribute.pdf", tmp_path)


def test_html_format_within_p(tmp_path):  # discussion 880
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", size=18)
    pdf.set_margins(20, 20, 100)
    pdf.write_html(
        """
<p align="justify">This is a sample text that will be justified
in the PDF. <u>This</u> is a <font color="red">sample text</font> that will be justified
in the PDF. <b>This</b> is a sample text that will be justified in the PDF.
<i>This</i> is a sample text that will be justified in the PDF.</p>
    """
    )
    assert_pdf_equal(pdf, HERE / "html_format_within_p.pdf", tmp_path)


def test_html_bad_font():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", size=18)
    with pytest.raises(FPDFException):
        pdf.write_html("""<font face="no_such_font"><p>hello helvetica</p></font>""")


def test_html_ln_outside_p(tmp_path):
    # Edge case. The <li> must come right after the </p> without anything
    # else in between (which would cause a new paragraph to be started).
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("times", size=18)
    pdf.write_html(
        """
            <p>someting in paragraph</p><li>causing _ln() outside paragraph</li>
    """
    )
    assert_pdf_equal(pdf, HERE / "html_ln_outside_p.pdf", tmp_path)


def test_html_and_section_title_styles():  # issue 1080
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.set_section_title_styles(TitleStyle("Helvetica", "B", 20, (0, 0, 0)))
    with pytest.raises(NotImplementedError):
        pdf.write_html(
            """
        <h1>Heading One</h1>
        <p>Just enough text to show how bad the situation really is</p>
        <h2>Heading Two</h2>
        <p>This will not overflow</p>
        """
        )


def test_html_link_color(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    html = '<a href="www.example.com">foo</a>'
    pdf.write_html(html, tag_styles={"a": FontFace(color=color_as_decimal("red"))})
    assert_pdf_equal(pdf, HERE / "html_link_color.pdf", tmp_path)


def test_html_blockquote_color(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    html = "Text before<blockquote>foo</blockquote>Text afterwards"
    pdf.write_html(html, tag_styles={"blockquote": FontFace(color=(125, 125, 0))})
    assert_pdf_equal(pdf, HERE / "html_blockquote_color.pdf", tmp_path)


def test_html_headings_color(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    html = "<h1>foo</h1><h2>bar</h2>"
    pdf.write_html(
        html,
        tag_styles={
            "h1": FontFace(color=(148, 139, 139), size_pt=24),
            "h2": FontFace(color=(148, 139, 139), size_pt=18),
        },
    )
    assert_pdf_equal(pdf, HERE / "html_headings_color.pdf", tmp_path)


def test_html_unsupported_tag_color():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(NotImplementedError):
        pdf.write_html("<p>foo</p>", tag_styles={"p": FontFace()})


def test_html_blockquote_indent(tmp_path):  # issue-1074
    pdf = FPDF()
    pdf.add_page()
    html = "Text before<blockquote>foo</blockquote>Text afterwards"
    pdf.write_html(html, tag_indents={"blockquote": 5})
    assert_pdf_equal(pdf, HERE / "html_blockquote_indent.pdf", tmp_path)


def test_html_li_tag_indent(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    with pytest.warns(DeprecationWarning):
        pdf.write_html("<ul><li>item</li></ul>", li_tag_indent=10)
    assert_pdf_equal(pdf, HERE / "html_li_tag_indent.pdf", tmp_path)


def test_html_ol_ul_line_height(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.write_html(
        """
    <p>Default line-height:</p>
    <ul>
        <li>item</li>
        <li>item</li>
        <li>item</li>
    </ul>
    <p>1.5 line-height:</p>
    <ol line-height="1.5">
        <li>item</li>
        <li>item</li>
        <li>item</li>
    </ol>
    <p>Double line-height:</p>
    <ul line-height="2">
        <li>item</li>
        <li>item</li>
        <li>item</li>
    </ul>
    <p>1.5 line-height as "style":</p>
    <ol style="line-height: 1.5">
        <li>item</li>
        <li>item</li>
        <li>item</li>
    </ol>
    <p>Double line-height as "style":</p>
    <ul style="line-height: 2">
        <li>item</li>
        <li>item</li>
        <li>item</li>
    </ul>"""
    )
    assert_pdf_equal(pdf, HERE / "html_ol_ul_line_height.pdf", tmp_path)
