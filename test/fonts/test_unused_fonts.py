import re
from pathlib import Path
import pypdf
from fpdf import FPDF

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE.parent / "fonts"


def get_used_fonts_in_page(page):
    content = page.get_contents()
    if isinstance(content, pypdf.generic.ArrayObject):
        content = b"".join([x.get_object().get_data() for x in content])
    else:
        content = content.get_data()
    font_refs = re.findall(rb"/F(\d+)", content)
    return {int(ref) for ref in font_refs}


def test_unused_fonts_not_included(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=FONT_DIR / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto", style="B", fname=FONT_DIR / "Roboto-Bold.ttf")  # F2
    pdf.add_font("Roboto", style="I", fname=FONT_DIR / "Roboto-Italic.ttf")  # F3
    pdf.set_font("Roboto", size=12)

    pdf.add_page()
    pdf.multi_cell(w=pdf.epw, text="**Text in bold**", markdown=True)  # use F2

    pdf.add_page()
    pdf.multi_cell(w=pdf.epw, text="__Text in italic__", markdown=True)  # use F3

    pdf.add_page()
    pdf.multi_cell(
        w=pdf.epw,
        text="Regular text\n**Text in bold**\n__Text in italic__",
        markdown=True,
    )  # use F1, F2, F3

    output_path = tmp_path / "test.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    assert len(reader.pages) == 3

    for page_num, page in enumerate(reader.pages, start=1):
        resources = page["/Resources"]
        fonts = resources.get("/Font", {})
        used_font_ids = get_used_fonts_in_page(page)
        for font_key in fonts:
            font_id = int(font_key[2:])  # /F1 -> 1
            assert (
                font_id in used_font_ids
            ), f"Page {page_num} contains unused font {font_key}"

        if page_num == 1:
            assert used_font_ids == {2}, "Page 1 should only use F2"
        elif page_num == 2:
            assert used_font_ids == {3}, "Page 2 should only use F3"
        elif page_num == 3:
            assert used_font_ids == {1, 2, 3}, "Page 3 should use F1, F2, F3"


def test_unused_added_font_not_included(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=FONT_DIR / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto-Bold", fname=FONT_DIR / "Roboto-Bold.ttf")  # F2

    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.cell(text="Hello")

    output_path = tmp_path / "test.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    fonts = reader.pages[0]["/Resources"]["/Font"]
    assert "F2" not in fonts, "Unused font F2 should not be included"


def test_font_set_but_not_used(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=FONT_DIR / "Roboto-Regular.ttf")  # F1
    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.add_page()
    pdf.set_font("Helvetica")
    pdf.cell(text="Hello")

    output_path = tmp_path / "test.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    page = reader.pages[0]
    # pylint: disable=no-member
    resources = page.get("/Resources", {})
    # pylint: enable=no-member
    page1_fonts = resources.get("/Font", {}) if isinstance(resources, dict) else {}
    assert not page1_fonts, "Page 1 should have no fonts as none were used"


def test_multiple_pages_font_usage(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=FONT_DIR / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto-Bold", fname=FONT_DIR / "Roboto-Bold.ttf")  # F2

    # Page 1: Use F1
    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.cell(text="Page 1")

    # Page 2: Use F2
    pdf.add_page()
    pdf.set_font("Roboto-Bold")
    pdf.cell(text="Page 2")

    output_path = tmp_path / "test.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    page1_fonts = reader.pages[0]["/Resources"]["/Font"]
    page2_fonts = reader.pages[1]["/Resources"]["/Font"]

    # pylint: disable=no-member
    assert list(page1_fonts.keys()) == ["/F1"], "Page 1 should only have F1"
    assert list(page2_fonts.keys()) == ["/F2"], "Page 2 should only have F2"
    # pylint: enable=no-member
