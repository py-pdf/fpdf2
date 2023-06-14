from pathlib import Path

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def test_indi_text(tmp_path):
    # issue #365
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Mangal", fname=HERE / "Mangal 400.ttf")
    pdf.set_font("Mangal", size=20)
    pdf.set_text_shaping(False)
    pdf.cell(txt="इण्टरनेट पर हिन्दी के साधन", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(txt="इण्टरनेट पर हिन्दी के साधन", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(
        pdf,
        HERE / "test_shaping_hindi.pdf",
        tmp_path,
    )


def test_text_replacement(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="FiraCode", fname=HERE / "FiraCode-Regular.ttf")
    pdf.set_font("FiraCode", size=20)
    pdf.set_text_shaping(False)
    pdf.cell(txt="http://www 3 >= 2 != 1", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(txt="http://www 3 >= 2 != 1", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(
        pdf,
        HERE / "test_text_replacement.pdf",
        tmp_path,
    )


def test_kerning(tmp_path):
    # issue #812
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Dumbledor3Thin", fname=HERE / "Dumbledor3Thin.ttf")
    pdf.set_font("Dumbledor3Thin", size=20)
    pdf.set_text_shaping(False)
    pdf.cell(txt="Ты То Тф Та Тт Ти", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(txt="Ты То Тф Та Тт Ти", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(
        pdf,
        HERE / "test_kerning.pdf",
        tmp_path,
    )
