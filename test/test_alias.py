from pathlib import Path

import pytest
import fpdf
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_alias_nb_pages(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Times")
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", align="C")
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", align="C")
    assert_pdf_equal(pdf, HERE / "alias_nb_pages.pdf", tmp_path)


def test_custom_alias_nb_pages(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Times")
    alias = "n{}b"
    pdf.alias_nb_pages(alias)
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{alias}", align="C")
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{alias}", align="C")
    assert_pdf_equal(pdf, HERE / "custom_alias_nb_pages.pdf", tmp_path)


def test_page_label(tmp_path):
    pdf = fpdf.FPDF()

    # title page - no numbering
    pdf.add_page(label_style="D")
    pdf.set_font("helvetica", "", 20)
    pdf.start_section("Title")
    pdf.cell(w=pdf.epw, text="TITLE", align="C")

    # pre-textual elements - lowercase roman numbering starting from 1
    pdf.add_page(label_style="r", label_start=1)
    pdf.set_font("helvetica", "", 14)
    pdf.start_section("Abstract")
    pdf.cell(text="Abstract")

    pdf.add_page()
    pdf.start_section("Table of contents")
    pdf.cell(text="Table of contents")

    pdf.add_page()
    pdf.start_section("List of figures and tables")
    pdf.cell(text="List of figures and tables")

    pdf.add_page()
    pdf.start_section("List of abbreviations")
    pdf.cell(text="List of abbreviations")

    pdf.add_page()
    pdf.start_section("Glossary")
    pdf.cell(text="Glossary")

    # textual elements - arabic numbers starting from 1
    pdf.add_page(label_style="D", label_start=1)
    pdf.set_font("helvetica", "", 14)
    pdf.start_section("Introduction")
    pdf.cell(text="Introduction")

    pdf.add_page()
    pdf.start_section("Literature review")
    pdf.cell(text="Literature review")

    pdf.add_page()
    pdf.start_section("Methodology")
    pdf.cell(text="Methodology")

    pdf.add_page()
    pdf.start_section("Results")
    pdf.cell(text="Results")

    pdf.add_page()
    pdf.start_section("Discussion")
    pdf.cell(text="Discussion")

    pdf.add_page()
    pdf.start_section("Conclusion")
    pdf.cell(text="Conclusion")

    pdf.add_page()
    pdf.start_section("Reference list")
    pdf.cell(text="Reference list")

    # appendices - prefix "A-" starting from 1
    pdf.add_page(label_style="D", label_prefix="A-", label_start=1)
    pdf.start_section("Appendices")
    pdf.cell(text="Appendix 1")

    pdf.add_page()
    pdf.cell(text="Appendix 2")

    pdf.add_page()
    pdf.cell(text="Appendix 3")

    pdf.add_page()
    pdf.cell(text="Appendix 4")

    pdf.add_page()
    pdf.cell(text="Appendix 5")

    assert_pdf_equal(pdf, HERE / "page_label.pdf", tmp_path)


def test_alias_with_shaping(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.add_page()
    pdf.set_font("Quicksand", size=24)
    pdf.set_text_shaping(True)
    pdf.write(text="Pages {nb}")
    pdf.ln()
    pdf.cell(text="{nb}", new_x="left", new_y="next")
    pdf.write_html("<h1>{nb}</h1>")
    pdf.multi_cell(w=pdf.epw, text="Number of pages: {nb}\nAgain:{nb}")
    pdf.add_page()
    pdf.set_text_shaping(False)
    pdf.write(text="Pages {nb}")
    pdf.ln()
    pdf.cell(text="{nb}", new_x="left", new_y="next")
    pdf.write_html("<h1>{nb}</h1>")
    pdf.multi_cell(w=pdf.epw, text="Number of pages: {nb}\nAgain:{nb}")
    assert_pdf_equal(pdf, HERE / "alias_with_text_shaping.pdf", tmp_path)


def test_alias_in_middle_with_shaping(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.add_page()
    pdf.set_font("Quicksand", size=24)
    pdf.set_text_shaping(True)
    pdf.write(text="Pages {nb} with shaping")
    pdf.ln()
    pdf.write(text="Pages {nb} with {nb} shaping")
    assert_pdf_equal(pdf, HERE / "alias_in_middle_with_shaping.pdf", tmp_path)


def test_alias_in_middle_with_shaping_many_pages(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.set_font("Quicksand", size=24)
    pdf.set_text_shaping(True)
    for _ in range(14):
        pdf.add_page()
        pdf.write(text="Pages {nb} with shaping")
        pdf.ln()
        pdf.write(text="Pages {nb} with {nb} shaping")
    assert_pdf_equal(
        pdf, HERE / "alias_in_middle_with_shaping_many_pages.pdf", tmp_path
    )


def test_alias_in_middle_with_shaping_markdown(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.add_font("Quicksand", style="B", fname=HERE / "fonts" / "Quicksand-Bold.otf")
    pdf.add_page()
    pdf.set_font("Quicksand", size=24)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text="**Pages {nb}** with shaping", markdown=True)
    assert_pdf_equal(pdf, HERE / "alias_in_middle_with_shaping_markdown.pdf", tmp_path)


def test_alias_overflow_warning():
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.set_font("Quicksand", size=24)
    pdf.set_text_shaping(True)
    pdf.alias_nb_pages("a")
    for _ in range(12):
        pdf.add_page()
        pdf.write(text="Page a")
    with pytest.warns(UserWarning, match="exceeds reserved dummy width"):
        pdf.output()
