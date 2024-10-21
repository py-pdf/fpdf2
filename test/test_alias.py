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


def test_alias_with_shaping(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_font("Quicksand", style="", fname=HERE / "fonts" / "Quicksand-Regular.otf")
    pdf.add_page()
    pdf.set_font("Quicksand", "", 24)
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
