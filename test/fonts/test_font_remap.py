from pathlib import Path

from fpdf import FPDF
from fpdf.fpdf import SubsetMap
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_subset_map():
    subset_map = SubsetMap(range(0, 1024, 2))
    assert len(subset_map.dict()) == 512

    for i in range(0, 1024, 2):
        assert i % 2 == 0
        assert i == subset_map.pick(i)

    for i in range(1023, 512, -2):
        assert subset_map.pick(i) % 2 == 1
    assert len(subset_map.dict()) == 512 + 256

    for i in range(1, 1000, 2):
        assert subset_map.pick(i) % 2 == 1

    assert len(subset_map.dict()) == 1024

    subset_dict = subset_map.dict()
    for i in subset_dict:
        for j in subset_dict:
            if i != j:
                assert subset_dict[i] != subset_dict[j]
            else:
                assert subset_dict[i] == subset_dict[i]


def test_emoji_glyph(tmp_path):
    pdf = FPDF()

    font_file_path = HERE / "DejaVuSans.ttf"
    pdf.add_font("DejaVuSans", fname=str(font_file_path))
    pdf.set_font("DejaVuSans", size=64)
    pdf.add_page()

    pdf.multi_cell(0, txt="".join([chr(0x1F600 + x) for x in range(68)]))

    pdf.set_font_size(32)
    pdf.text(10, 270, "".join([chr(0x1F0A0 + x) for x in range(15)]))

    assert_pdf_equal(pdf, HERE / "fonts_emoji_glyph.pdf", tmp_path)


def test_nb_replace(tmp_path):
    pdf = FPDF()

    font_file_path = HERE / "DejaVuSans.ttf"
    pdf.add_font("DejaVuSans", fname=str(font_file_path))
    pdf.add_page()

    pdf.set_font("DejaVuSans", size=64)
    pdf.cell(txt="{nb}")

    pdf.set_font("helvetica")
    pdf.cell(txt="{nb}")

    assert_pdf_equal(pdf, HERE / "fonts_remap_nb.pdf", tmp_path)


def test_two_mappings(tmp_path):
    pdf = FPDF()

    font_file_path_1 = HERE / "DejaVuSans.ttf"
    font_file_path_2 = HERE / "DroidSansFallback.ttf"
    pdf.add_font("DejaVuSans", fname=str(font_file_path_1))
    pdf.add_font("DroidSansFallback", fname=str(font_file_path_2))
    pdf.add_page()

    pdf.set_font("DejaVuSans", size=64)
    pdf.cell(txt="ABCDEF")

    pdf.set_font("DroidSansFallback")
    pdf.cell(txt="DEFGHI")

    assert_pdf_equal(pdf, HERE / "fonts_two_mappings.pdf", tmp_path)


def test_thai_text(tmp_path):
    pdf = FPDF()
    pdf.add_font("Waree", fname=HERE / "Waree.ttf")
    pdf.set_font("Waree")
    pdf.add_page()
    pdf.write(txt="สวัสดีชาวโลก ทดสอบฟอนต์, Hello world font test.")
    assert_pdf_equal(pdf, HERE / "thai_text.pdf", tmp_path)
