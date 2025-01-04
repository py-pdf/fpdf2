from pathlib import Path
from fpdf import FPDF
from fpdf.pattern import RadialGradient
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_radial_gradient(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.w / 2 - 25
    y = pdf.get_y()
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            x + 25,
            y + 25,
            0,
            x + 25,
            y + 25,
            25,
            [(255, 255, 0), (255, 0, 0)],
        )
    ):
        pdf.circle(x=x + 25, y=y + 25, radius=25, style="FD")
    y += 60
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            x + 5,
            y + 5,
            0,
            x + 25,
            y + 25,
            25,
            [(255, 255, 0), (255, 0, 0)],
        )
    ):
        pdf.circle(x=x + 25, y=y + 25, radius=25, style="FD")

    assert_pdf_equal(pdf, HERE / "radial_gradient.pdf", tmp_path)


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

    assert_pdf_equal(pdf, HERE / "radial_gradient_multiple_colors.pdf", tmp_path)


def test_radial_gradient(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.w / 2 - 25
    y = pdf.get_y()
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            x + 25,
            y + 25,
            0,
            x + 25,
            y + 25,
            25,
            [(255, 255, 0), (255, 0, 0)],
        )
    ):
        pdf.circle(x=x + 25, y=y + 25, radius=25, style="FD")
    y += 60
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            x + 5,
            y + 5,
            0,
            x + 25,
            y + 25,
            25,
            [(255, 255, 0), (255, 0, 0)],
        )
    ):
        pdf.circle(x=x + 25, y=y + 25, radius=25, style="FD")

    assert_pdf_equal(pdf, HERE / "radial_gradient.pdf", tmp_path)


def test_custom_bounds(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    with pdf.use_pattern(
        RadialGradient(
            pdf,
            pdf.w / 2,
            pdf.h / 2,
            20,
            pdf.w / 2,
            pdf.h / 2,
            pdf.h / 2 - 20,
            [
                "#FFFFFF",
                "#9400D3",
                "#4B0082",
                "#0000FF",
                "#00FF00",
                "#FFFF00",
                "#FF7F00",
                "#FF0000",
                "#FFFFFF",
            ],
            bounds=[0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65],
        )
    ):
        pdf.rect(x=0, y=0, w=pdf.w, h=pdf.h / 2, style="FD")

    assert_pdf_equal(pdf, HERE / "radial_custom_bounds.pdf", tmp_path)
