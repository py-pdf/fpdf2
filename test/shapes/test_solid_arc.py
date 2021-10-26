from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def next_row(pdf):
    pdf.ln()
    pdf.set_y(pdf.get_y() + size + margin)


size = 50
start_angle, end_angle = 30, 130
margin = 10


def test_solid_arc_not_circle(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for counter, style in enumerate(["F", "FD", "DF", None]):
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size / 2,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            style=style,
        )
        pdf.set_x(pdf.get_x() + (size / 2) + margin)
        if counter % 3 == 0:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_not_circle.pdf", tmp_path)


def test_solid_arc_style(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for counter, style in enumerate(["F", "FD", "DF", None]):
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            style=style,
        )
        pdf.set_x(pdf.get_x() + size + margin)
        if counter % 3 == 0:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_style.pdf", tmp_path)


def test_solid_arc_line_width(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    size_1 = size

    for line_width in [1, 2, 3]:
        pdf.set_line_width(line_width)
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            # A workaround to avoid warning of pylint triggering duplicate code
            # with test_arc.py
            a=size_1,
            b=size_1,
            start_angle=start_angle,
            end_angle=end_angle,
            style=None,
        )
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)
    for line_width in [4, 5, 6]:
        pdf.set_line_width(line_width)
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            style=None,
        )
        pdf.set_x(pdf.get_x() + size + margin)
    pdf.set_line_width(0.2)  # reset

    assert_pdf_equal(pdf, HERE / "class_solid_arc_line_width.pdf", tmp_path)


def test_solid_arc_draw_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_line_width(0.5)
    for gray in [70, 140, 210]:
        pdf.set_draw_color(gray)
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            style=None,
        )
        pdf.set_x(pdf.get_x() + size + margin)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_draw_color.pdf", tmp_path)


def test_solid_arc_fill_color(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    pdf.set_fill_color(240)
    for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
        pdf.set_draw_color(*color)
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            style="FD",
        )
        pdf.set_x(pdf.get_x() + size + margin)
    next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_fill_color.pdf", tmp_path)


def test_solid_arc_inclination(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    size_1 = size

    for counter, inclination in enumerate([0, 30, 90, 120]):
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            # A workaround to avoid warning of pylint triggering duplicate code
            # with test_arc.py
            a=size_1,
            b=size_1,
            start_angle=start_angle,
            end_angle=end_angle,
            inclination=inclination,
            style=None,
        )
        pdf.set_x(pdf.get_x() + size + margin)
        if counter % 3 == 0:
            next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_inclination.pdf", tmp_path)


def test_arc_clockwise(tmp_path):
    pdf = fpdf.FPDF(unit="mm")
    pdf.add_page()

    for inclination in [0, 30, 90, 120]:
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            inclination=inclination,
            style=None,
        )
        pdf.set_x(pdf.get_x() + size + margin)
        pdf.solid_arc(
            x=pdf.get_x(),
            y=pdf.get_y(),
            a=size,
            b=size,
            start_angle=start_angle,
            end_angle=end_angle,
            inclination=inclination,
            clockwise=True,
            style=None,
        )
        next_row(pdf)

    assert_pdf_equal(pdf, HERE / "class_solid_arc_clockwise.pdf", tmp_path)
