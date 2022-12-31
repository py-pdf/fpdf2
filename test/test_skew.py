from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def test_skew(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x, y = 60, 60
    img_filepath = HERE / "image/png_images/66ac49ef3f48ac9482049e1ab57a53e9.png"
    with pdf.skew(ax=45, x=x, y=y):
        pdf.image(img_filepath, x=x, y=y)
    with pdf.skew(ax=45, ay=30, x=x+20, y=y-20):
        pdf.image(img_filepath, x=x+20, y=y-20)
    pdf.set_line_width(2)
    pdf.set_draw_color(240)
    pdf.set_fill_color(r=230, g=30, b=180)
    with pdf.skew(ax=-45, ay=0, x=100, y=170):
        pdf.circle(x=100, y=170, r=10, style="FD")
    pdf.image(img_filepath, x=150, y=150)
    assert_pdf_equal(pdf, HERE / "skew.pdf", tmp_path)


def test_skew_text(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    with doc.skew(0, 20, 20, 20):
        doc.text(20, 20, txt="text skewed on the y-axis")
    with doc.skew(0, -20, 20, 60):
        doc.text(20, 60, txt="text skewed on the y-axis (negative)")
        doc.text(20, 100, txt="text skewed on the y-axis (negative) - line 2")
    with doc.skew(20, 0, 20, 140):
        doc.text(20, 140, txt="text skewed on the x-axis")
    with doc.skew(-20, 0, 20, 180):
        doc.text(20, 180, txt="text skewed on the x-axis (negative)")
    with doc.skew(89, 0, 20, 220):
        doc.text(20, 220, txt="some extreme skewing")
    assert_pdf_equal(doc, HERE / "skew_text.pdf", tmp_path)


def test_cell_skew_text(tmp_path):
    doc = FPDF()
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.ln(40)
    with doc.skew(0, 20):
        doc.cell(txt="text skewed on the y-axis")
        doc.ln(40)
    with doc.skew(0, -20):
        doc.cell(txt="text skewed on the y-axis (negative)")
        doc.ln(40)
    with doc.skew(20, 0):
        doc.cell(txt="text skewed on the x-axis")
        doc.ln(40)
    with doc.skew(-20, 0):
        doc.cell(txt="text skewed on the x-axis (negative)")
        doc.ln(40)
    with doc.skew(89, 0):
        doc.cell(txt="some extreme skewing")
        doc.ln(40)
    assert_pdf_equal(doc, HERE / "cell_skew_text.pdf", tmp_path)


def test_multi_cell_skew_text(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    # built-in font
    pdf.set_font("Helvetica", "", 8)
    pdf.set_fill_color(255, 255, 0)
    with pdf.skew(20, 0):
        pdf.multi_cell(w=150, txt=LOREM_IPSUM[:200], fill=True)
        pdf.ln(60)
    with pdf.skew(0, 20):
        pdf.multi_cell(w=150, txt=LOREM_IPSUM[:200], fill=True)
        pdf.ln(60)
    with pdf.skew(20, 20):
        pdf.multi_cell(w=150, txt=LOREM_IPSUM[:200], fill=True)
    assert_pdf_equal(pdf, HERE / "multi_cell_skew_text.pdf", tmp_path)
