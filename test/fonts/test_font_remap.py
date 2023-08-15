from pathlib import Path

from fpdf import FPDF

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_emoji_glyph(tmp_path):
    pdf = FPDF()

    pdf.add_font(fname=HERE / "DejaVuSans.ttf")
    pdf.set_font("DejaVuSans", size=64)
    pdf.add_page()

    pdf.multi_cell(0, txt="".join([chr(0x1F600 + x) for x in range(68)]))

    pdf.set_font_size(32)
    pdf.text(10, 270, "".join([chr(0x1F0A0 + x) for x in range(15)]))

    assert_pdf_equal(pdf, HERE / "fonts_emoji_glyph.pdf", tmp_path)


def test_nb_replace(tmp_path):
    pdf = FPDF()

    pdf.add_font(fname=HERE / "DejaVuSans.ttf")
    pdf.add_page()

    pdf.set_font("DejaVuSans", size=64)
    pdf.cell(txt="{nb}")

    pdf.set_font("helvetica")
    pdf.cell(txt="{nb}")

    assert_pdf_equal(pdf, HERE / "fonts_remap_nb.pdf", tmp_path)


def test_two_mappings(tmp_path):
    pdf = FPDF()

    pdf.add_font(fname=HERE / "DejaVuSans.ttf")
    pdf.add_font(fname=HERE / "DroidSansFallback.ttf")
    pdf.add_page()

    pdf.set_font("DejaVuSans", size=64)
    pdf.cell(txt="ABCDEF")

    pdf.set_font("DroidSansFallback")
    pdf.cell(txt="DEFGHI")

    assert_pdf_equal(pdf, HERE / "fonts_two_mappings.pdf", tmp_path)


def test_thai_text(tmp_path):
    pdf = FPDF()
    pdf.add_font(fname=HERE / "Waree.ttf")
    pdf.set_font("Waree")
    pdf.add_page()
    pdf.write(txt="สวัสดีชาวโลก ทดสอบฟอนต์, Hello world font test.")
    assert_pdf_equal(pdf, HERE / "thai_text.pdf", tmp_path)
