from pathlib import Path
from fpdf import FPDF
from fpdf.pattern import RadialGradient
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_radial_gradient_multiple_colors(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            (pdf.epw + pdf.l_margin) / 2,
            y + 50,
            20,
            (pdf.epw + pdf.l_margin) / 2,
            y + 50,
            (pdf.epw + pdf.l_margin) / 2,
            ["#868F96", "#596164", "#537895", "#09203F"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=100, style="FD")
    y += 105

    with pdf.use_pattern(
        RadialGradient(
            pdf,
            pdf.w / 2,
            y + 50,
            0,
            pdf.w / 2,
            y + 50,
            (y + 50) / 2,
            ["#FFECD2", "#FCB69F", "#DD2476"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=100, style="FD")

    assert_pdf_equal(
        pdf, HERE / "radial_gradient_multiple_colors.pdf", tmp_path, generate=True
    )
