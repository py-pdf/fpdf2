from pathlib import Path
from fpdf import FPDF
from fpdf.pattern import LinearGradient
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_linear_gradient_extend(tmp_path):
    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("helvetica", "", 20)
    pdf.cell(
        text="Creating a gradient slightly smaller than the rectangle",
        new_x="LEFT",
        new_y="NEXT",
    )
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin + 10,
            0,
            pdf.epw + pdf.l_margin - 10,
            0,
            ["#C33764", "#1D2671"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")
        y += 25
        pdf.set_y(y)
        pdf.set_font("helvetica", "", 40)
        pdf.cell(
            text="LINEAR GRADIENT", align="C", w=pdf.epw, new_x="LEFT", new_y="NEXT"
        )

    pdf.ln()
    pdf.set_font("helvetica", "", 20)
    pdf.cell(text="Adding a background color", new_x="LEFT", new_y="NEXT")
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin + 10,
            0,
            pdf.epw + pdf.l_margin - 10,
            0,
            ["#C33764", "#1D2671"],
            background="#868F96",
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")
        y += 25
        pdf.set_y(y)
        pdf.set_font("helvetica", "", 40)
        pdf.cell(
            text="LINEAR GRADIENT", align="C", w=pdf.epw, new_x="LEFT", new_y="NEXT"
        )

    pdf.ln()
    pdf.set_font("helvetica", "", 20)
    pdf.cell(text="Adding extend before", new_x="LEFT", new_y="NEXT")
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin + 10,
            0,
            pdf.epw + pdf.l_margin - 10,
            0,
            ["#C33764", "#1D2671"],
            background="#868F96",
            extend_before=True,
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")
        y += 25
        pdf.set_y(y)
        pdf.set_font("helvetica", "", 40)
        pdf.cell(
            text="LINEAR GRADIENT", align="C", w=pdf.epw, new_x="LEFT", new_y="NEXT"
        )

    pdf.ln()
    pdf.set_font("helvetica", "", 20)
    pdf.cell(text="Adding extend after", new_x="LEFT", new_y="NEXT")
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin + 10,
            0,
            pdf.epw + pdf.l_margin - 10,
            0,
            ["#C33764", "#1D2671"],
            background="#868F96",
            extend_before=True,
            extend_after=True,
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")
        y += 25
        pdf.set_y(y)
        pdf.set_font("helvetica", "", 40)
        pdf.cell(
            text="LINEAR GRADIENT", align="C", w=pdf.epw, new_x="LEFT", new_y="NEXT"
        )

    assert_pdf_equal(
        pdf,
        HERE / "linear_gradient_extend.pdf",
        tmp_path,
    )


def test_linear_gradient_multiple_colors(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin,
            0,
            pdf.epw + pdf.l_margin,
            0,
            ["#868F96", "#596164", "#537895", "#09203F"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")
    y += 25

    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin,
            0,
            pdf.epw + pdf.l_margin,
            0,
            ["#FFECD2", "#FCB69F", "#DD2476"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=20, style="FD")

    assert_pdf_equal(
        pdf,
        HERE / "linear_gradient_multiple_colors.pdf",
        tmp_path,
    )


def test_linear_gradient_vertical(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            0,
            y,
            0,
            y + 50,
            ["#92EFFD", "#4E65FF"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=50, style="FD")
    y += 55

    with pdf.use_pattern(
        LinearGradient(
            0,
            y,
            0,
            y + 50,
            ["#FFECD2", "#FCB69F", "#DD2476"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=50, style="FD")

    assert_pdf_equal(pdf, HERE / "linear_gradient_vertical.pdf", tmp_path)


def test_linear_gradient_diagonal(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    x = pdf.l_margin
    y = pdf.get_y()
    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin,
            y,
            pdf.epw + pdf.l_margin,
            y + 100,
            ["#92EFFD", "#4E65FF"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=100, style="FD")
    y += 105

    with pdf.use_pattern(
        LinearGradient(
            pdf.l_margin,
            y + 100,
            pdf.epw + pdf.l_margin,
            y,
            ["#FFECD2", "#DD2476", "#FCB69F"],
        )
    ):
        pdf.rect(x=x, y=y, w=pdf.epw, h=100, style="FD")

    assert_pdf_equal(
        pdf,
        HERE / "linear_gradient_diagonal.pdf",
        tmp_path,
    )
