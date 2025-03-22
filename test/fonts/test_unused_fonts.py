# pylint: disable=no-member
import re
from pathlib import Path
import pypdf
from fpdf import FPDF

HERE = Path(__file__).resolve().parent


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
    pdf.add_font("Roboto", fname=HERE / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto", fname=HERE / "Roboto-Bold.ttf", style="B")  # F2
    pdf.add_font("Roboto", fname=HERE / "Roboto-Italic.ttf", style="I")  # F3
    pdf.add_font("Roboto", fname=HERE / "Roboto-BoldItalic.TTF", style="BI")  # F4
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

    output_path = tmp_path / "throwaway.pdf"
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
    pdf.add_font("Roboto", fname=HERE / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto", fname=HERE / "Roboto-Bold.ttf", style="B")  # F2

    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.cell(text="Hello")

    output_path = tmp_path / "throwaway.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    fonts = reader.pages[0]["/Resources"]["/Font"]
    assert "F2" not in fonts, "Unused font F2 should not be included"


def test_font_set_but_not_used(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=HERE / "Roboto-Regular.ttf")  # F1
    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.add_page()
    pdf.set_font("Helvetica")
    pdf.cell(text="Hello")

    output_path = tmp_path / "throwaway.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    page = reader.pages[0]
    resources = page.get("/Resources", {})
    page1_fonts = resources.get("/Font", {}) if isinstance(resources, dict) else {}
    assert not page1_fonts, "Page 1 should have no fonts as none were used"


def test_multiple_pages_font_usage(tmp_path):
    pdf = FPDF()
    pdf.add_font("Roboto", fname=HERE / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto", fname=HERE / "Roboto-Bold.ttf", style="B")  # F2

    # Page 1: Use F1
    pdf.add_page()
    pdf.set_font("Roboto")
    pdf.cell(text="Page 1")

    # Page 2: Use F2
    pdf.add_page()
    pdf.set_font(style="B")
    pdf.cell(text="Page 2")

    output_path = tmp_path / "throwaway.pdf"
    pdf.output(output_path)

    reader = pypdf.PdfReader(output_path)
    page1_fonts = reader.pages[0]["/Resources"]["/Font"]
    page2_fonts = reader.pages[1]["/Resources"]["/Font"]

    assert list(page1_fonts.keys()) == ["/F1"], "Page 1 should only have F1"
    assert list(page2_fonts.keys()) == ["/F2"], "Page 2 should only have F2"


def test_nested_context_font_usage_after_page_break(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=HERE / "Roboto-Regular.ttf")  # F1
    pdf.add_font("Roboto", fname=HERE / "Roboto-BoldItalic.TTF", style="BI")  # F2
    pdf.add_font(fname=HERE / "DejaVuSans.ttf")  # F3
    pdf.add_font(fname=HERE / "Garuda.ttf")  # F4
    font_mapping = {
        1: "Roboto-Regular",
        2: "Roboto-BoldItalic",
        3: "DejaVuSans",
        4: "Garuda",
    }

    # Outer context A
    with pdf.local_context():
        pdf.set_font("Roboto", size=12)
        pdf.write(text="A1 Roboto-Regular\n")

        # Context B
        with pdf.local_context():
            pdf.set_font(style="BI", size=14)
            pdf.write(text="B1 Roboto-BoldItalic\n")

            # Context C
            with pdf.local_context():
                pdf.set_font("DejaVuSans", style="", size=16)
                pdf.write(text="C1 DejaVuSans\n")

                # Context D - will trigger page break
                with pdf.local_context():
                    pdf.set_font("Garuda", size=18)
                    # Generate enough text to force page break
                    long_text = "D1 " + "D2Garuda " * 250  # ~100 words
                    pdf.multi_cell(w=pdf.epw, text=long_text)  # page break

                # After break: C context resumes but writes nothing

            # After break: B context resumes
            pdf.write(text="B2 ")  # Should use Roboto-BoldItalic again

        # After break: A context resumes
        pdf.write(text="A2 ")  # Should use Roboto again

    pdf.output(tmp_path / "test_nested_context_font_usage_after_page_break.pdf")

    reader = pypdf.PdfReader(
        tmp_path / "test_nested_context_font_usage_after_page_break.pdf"
    )
    assert len(reader.pages) == 2, "The PDF produced should have 2 pages"

    page1 = reader.pages[0]
    page1_used_fonts = set(font_mapping[f] for f in get_used_fonts_in_page(page1))
    page1_used_fonts_str = "Fonts used: " + ", ".join(page1_used_fonts)
    assert len(page1_used_fonts) == 4, (
        "Page 1 should use all fonts - " + page1_used_fonts_str
    )

    page2 = reader.pages[1]
    page2_used_fonts = set(font_mapping[f] for f in get_used_fonts_in_page(page2))
    page2_used_fonts_str = "Fonts used: " + ", ".join(page2_used_fonts)
    assert page2_used_fonts == {"Roboto-Regular", "Roboto-BoldItalic", "Garuda"}, (
        "Page 2 should use 3 fonts - " + page2_used_fonts_str
    )

    page2_resources = page2["/Resources"].get("/Font", {})
    for font_key in page2_resources:
        font_id = int(font_key[2:])  # convert /F1 -> 1
        font_name = font_mapping[font_id]
        assert (
            font_name in page2_used_fonts
        ), f"page 2 resource includes unused font：{font_name}（F{font_id}）"
