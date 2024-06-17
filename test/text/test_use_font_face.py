from pathlib import Path

from fpdf import FPDF, FontFace

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_header_footer_and_use_font_face(tmp_path):  # issue 1204
    class PDF(FPDF):
        def header(self):
            with self.use_font_face(FontFace(color="#00ff00", size_pt=12)):  # LABEL A
                self.cell(text=f"Header {self.page_no()}")
            self.ln()

        def footer(self):
            self.set_y(-15)
            with self.use_font_face(FontFace(color="#0000ff", size_pt=12)):  # LABEL B
                self.cell(text=f"Footer {self.page_no()}")

    pdf = PDF()
    pdf.set_font(family="helvetica", size=12)
    pdf.add_page()
    with pdf.use_font_face(FontFace(size_pt=36)):  # LABEL C
        pdf.multi_cell(w=0, text="\n".join(f"Line {i + 1}" for i in range(21)))
    assert pdf.font_size_pt == 12
    assert_pdf_equal(pdf, HERE / "header_footer_and_use_font_face.pdf", tmp_path)
