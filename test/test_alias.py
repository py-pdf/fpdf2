from pathlib import Path

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
    # Prerequisite to get exactly the same output in the PDF:
    # the default alias and the new one must be of same width:
    assert pdf.get_string_width(pdf.str_alias_nb_pages) == pdf.get_string_width(alias)
    pdf.alias_nb_pages(alias)
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{alias}", align="C")
    pdf.add_page()
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{alias}", align="C")
    assert_pdf_equal(pdf, HERE / "alias_nb_pages.pdf", tmp_path)


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
