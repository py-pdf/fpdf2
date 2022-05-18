from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal
from fpdf.drawing import DeviceGray


HERE = Path(__file__).resolve().parent


def test_add_page_format(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    for i in range(9):
        pdf.add_page(format=(210 * (1 - i / 10), 297 * (1 - i / 10)))
        pdf.cell(w=10, h=10, txt=str(i))
    pdf.add_page(same=True)
    pdf.cell(w=10, h=10, txt="9")
    assert_pdf_equal(pdf, HERE / "add_page_format.pdf", tmp_path)


def test_add_page_duration(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica", size=120)
    pdf.add_page(duration=3)
    pdf.cell(txt="Page 1")
    pdf.page_duration = 0.5
    pdf.add_page()
    pdf.cell(txt="Page 2")
    pdf.add_page()
    pdf.cell(txt="Page 3")
    assert_pdf_equal(pdf, HERE / "add_page_duration.pdf", tmp_path)


def test_break_or_add_page(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_auto_page_break(auto=True, margin=0)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 16)
    for i in range(1, 51):
        pdf.set_x(10)
        pdf.multi_cell(50, 10, f"Text {i} - Page {pdf.page}", 1, "C")
    pdf.page = 1
    pdf.set_xy(100, 10)
    for i in range(51, 101):
        pdf.set_x(100)
        pdf.multi_cell(50, 10, f"Text {i} - Page {pdf.page}", 1, "C")
    assert_pdf_equal(pdf, HERE / "break_or_add_page.pdf", tmp_path)


def test_break_or_add_page_with_different_draw_and_fill_color(tmp_path):
    class CustomHeader(fpdf.FPDF):
        def header(self):
            self.line_width = 0
            self.draw_color = DeviceGray(0.2)
            self.fill_color = DeviceGray(0.2)

    pdf = CustomHeader()
    pdf.set_auto_page_break(auto=True, margin=0)
    pdf.draw_color = DeviceGray(0.5)
    pdf.set_stretching(101)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 16)
    for i in range(1, 51):
        pdf.set_x(10)
        pdf.multi_cell(50, 10, f"Text {i} - Page {pdf.page}", 1, "C")
    pdf.page = 1
    pdf.set_xy(100, 10)
    for i in range(51, 101):
        pdf.set_x(100)
        pdf.multi_cell(50, 10, f"Text {i} - Page {pdf.page}", 1, "C")
    assert_pdf_equal(pdf, HERE / "break_or_add_page_draw_fill.pdf", tmp_path)
