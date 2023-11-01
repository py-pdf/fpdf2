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
        pdf.cell(w=10, h=10, text=str(i))
    pdf.add_page(same=True)
    pdf.cell(w=10, h=10, text="9")
    assert_pdf_equal(pdf, HERE / "add_page_format.pdf", tmp_path)


def test_add_page_duration(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica", size=120)
    pdf.add_page(duration=3)
    pdf.cell(text="Page 1")
    pdf.page_duration = 0.5
    pdf.add_page()
    pdf.cell(text="Page 2")
    pdf.add_page()
    pdf.cell(text="Page 3")
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


def test_new_page_graphics_state(tmp_path):
    # Make sure that on a page break, all graphics state items are
    # carried over correctly.
    # issue #992 - dash patterns were not handled correctly.
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    pdf.set_font("Courier", "iu", 16)
    pdf.set_draw_color(255, 100, 0)
    pdf.set_fill_color(100, 255, 0)
    pdf.set_text_color(0, 0, 255)
    # underline -> set_font()
    # font_style -> set_font()
    pdf.set_stretching(50)
    pdf.set_char_spacing(5)
    # font_family -> set_font()
    # font_size_pt -> set_font()
    # current_font -> set_font()
    pdf.set_dash_pattern(dash=2, gap=4)
    pdf.set_line_width(2)
    # text_mode -> applied via Fragments
    # char lift/scale -> applied via Fragments
    # text_shaping -> applied in the creation of Fragments

    def draw_stuff():
        pdf.cell(
            text="This text is blue, italic, underlined, and squished with wide char spacing.",
            new_x="LEFT",
            new_y="NEXT",
        )
        pdf.cell(text="The box below is green, with a thick, dashed, orange border.")
        pdf.rect(50, 50, 60, 30, style="DF")

    draw_stuff()
    pdf.add_page()
    draw_stuff()
    assert_pdf_equal(pdf, HERE / "new_page_graphics_state.pdf", tmp_path)
