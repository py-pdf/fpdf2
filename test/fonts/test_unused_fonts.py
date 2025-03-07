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


def test_nested_context_font_usage_after_page_break(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto-Regular", style="", fname=HERE / "Roboto-Regular.ttf")
    pdf.add_font("Roboto-BoldItalic", style="", fname=HERE / "Roboto-BoldItalic.TTF")
    pdf.add_font("DejaVuSans", style="", fname=HERE / "DejaVuSans.ttf")
    pdf.add_font("Garuda", style="", fname=HERE / "Garuda.ttf")

    # Outer context A
    with pdf.local_context():
        pdf.set_font("Roboto-Regular", size=12)
        pdf.write(text="A1 Roboto-Regular\n")

        # Context B
        with pdf.local_context():
            pdf.set_font("Roboto-BoldItalic", size=14)
            pdf.write(text="B1 Roboto-BoldItalic\n")

            # Context C
            with pdf.local_context():
                pdf.set_font("DejaVuSans", size=16)
                pdf.write(text="C1 DejaVuSans\n")

                # Context D - will trigger page break
                with pdf.local_context():
                    pdf.set_font("Garuda", size=18)
                    # Generate enough text to force page break
                    long_text = "D1 " + "D2Garuda " * 250  # ~100 words
                    pdf.multi_cell(w=pdf.epw, text=long_text)  # This will break page

                # After break: C context resumes but writes nothing

            # After break: B context resumes but writes nothing

        # After break: A context resumes
        pdf.write(text="A2 ")  # Should use Roboto again

    pdf.output(tmp_path / "test_nested_context_font_usage_after_page_break.pdf")

    reader = pypdf.PdfReader(
        tmp_path / "test_nested_context_font_usage_after_page_break.pdf"
    )
    assert len(reader.pages) == 2, "There should be 2 pages"

    font_mapping = {
        1: "Roboto-Regular",
        2: "Roboto-BoldItalic",
        3: "DejaVuSans",
        4: "Garuda",
    }

    page1 = reader.pages[0]
    page1_used_fonts = get_used_fonts_in_page(page1)
    print("Fonts used in page 1:", [font_mapping[f] for f in page1_used_fonts])

    page2 = reader.pages[1]
    page2_used_fonts = get_used_fonts_in_page(page2)
    print("Fonts used in page 2:", [font_mapping[f] for f in page2_used_fonts])

    assert page2_used_fonts == {1, 4}, "page 2 should only use font 1 and 4"

    # pylint: disable=no-member
    page2_resources = page2["/Resources"].get("/Font", {})
    # pylint: enable=no-member
    for font_key in page2_resources:
        font_id = int(font_key[2:])  # convert /F1 -> 1
        assert (
            font_id in page2_used_fonts
        ), f"page 2 resource includes unused font：{font_mapping[font_id]}（F{font_id}）"
