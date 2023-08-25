import math
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import Angle
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def draw_mirror_line(pdf, origin, angle):
    """
    A helper method which converts a given angle and origin to two co-ordinates to
    then draw a line.
    Used to help visualize & test mirror transformations.

    Args:
        pdf (fpdf.FPDF): pdf to modify
        origin (float, Sequence[float, float]): a point on the mirror line
        angle: (fpdf.enums.Angle): the direction of the mirror line
    """
    x, y = origin
    try:
        theta = Angle.coerce(angle).value
    except ValueError:
        theta = angle

    cos_theta, sin_theta = (
        math.cos(math.radians(theta)),
        math.sin(math.radians(theta)) * -1,
    )

    x1 = x - (150 * cos_theta)
    y1 = y - (150 * sin_theta)
    x2 = x + (150 * cos_theta)
    y2 = y + (150 * sin_theta)
    pdf.line(x1=x1, y1=y1, x2=x2, y2=y2)


def test_mirror(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_line_width(0.5)
    pdf.set_draw_color(r=255, g=128, b=0)

    img_filepath = HERE / "image/png_images/66ac49ef3f48ac9482049e1ab57a53e9.png"

    pdf.image(img_filepath, x=100, y=100)

    pdf.image(img_filepath, x=100, y=100)
    with pdf.mirror((pdf.epw / 2, pdf.eph / 2.5), "WEST"):
        draw_mirror_line(pdf, (pdf.epw / 2, pdf.eph / 2.5), "WEST")
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror((pdf.epw / 2.5, pdf.eph / 2), "SOUTH"):
        pdf.set_draw_color(r=128, g=0, b=0)
        draw_mirror_line(pdf, (pdf.epw / 2.5, pdf.eph / 2), "SOUTH")
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror((pdf.epw / 1.5, pdf.eph / 1.5), "SOUTHWEST"):
        pdf.set_draw_color(r=0, g=0, b=128)
        draw_mirror_line(pdf, (pdf.epw / 1.5, pdf.eph / 1.5), "SOUTHWEST")
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror((pdf.epw / 3, pdf.eph / 2.5), "SOUTHEAST"):
        pdf.set_draw_color(r=0, g=128, b=0)
        draw_mirror_line(pdf, (pdf.epw / 3, pdf.eph / 2.5), "SOUTHEAST")
        pdf.image(img_filepath, x=100, y=100)

    assert_pdf_equal(pdf, HERE / "mirror.pdf", tmp_path)


def test_mirror_with_angle_as_number(tmp_path):
    pdf = FPDF()
    pdf.set_font("helvetica", size=50)
    pdf.add_page()
    x, y = 50, 50
    pdf.text(x, y, text="mirror this text")
    with pdf.mirror((x, y), 180):
        pdf.set_text_color(r=255, g=128, b=0)
        pdf.text(x, y, text="mirror this text")
    assert_pdf_equal(pdf, HERE / "mirror_with_angle_as_number.pdf", tmp_path)


def test_mirror_text(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    pdf.text(pdf.epw / 2, pdf.epw / 2, text="mirror this text")

    with pdf.mirror((pdf.epw / 2, pdf.eph / 2.5), "EAST"):
        pdf.text(pdf.epw / 2, pdf.eph / 2, text="mirrored text E/W")

    with pdf.mirror((pdf.epw / 2.5, pdf.eph / 2), "NORTH"):
        pdf.text(pdf.epw / 2, pdf.eph / 2, text="mirrored text N/S")

    with pdf.mirror((pdf.epw / 1.5, pdf.eph / 1.5), "NORTHWEST"):
        pdf.text(pdf.epw / 2, pdf.eph / 2, text="mirrored text NW/SE")

    with pdf.mirror((pdf.epw / 2.5, pdf.eph / 2.5), "NORTHEAST"):
        pdf.text(pdf.epw / 2, pdf.eph / 2, text="mirrored text NE/SW")

    assert_pdf_equal(pdf, HERE / "mirror_text.pdf", tmp_path)


def test_mirror_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.set_fill_color(255, 255, 0)

    pdf.cell(text="cell to be mirrored repeatedly")
    pdf.x = pdf.l_margin
    with pdf.mirror((pdf.epw / 2, 0), "NORTH"):
        draw_mirror_line(pdf, (pdf.epw / 2, 0), "NORTH")
        pdf.cell(text="cell mirrored", fill=True)
        pdf.cell(text="cell mirrored", fill=True)
        pdf.cell(text="cell mirrored", fill=True)
        pdf.ln(40)

    pdf.cell(text="cell text 1")
    pdf.x = pdf.l_margin
    with pdf.mirror((pdf.epw / 2, pdf.eph / 4), "EAST"):
        draw_mirror_line(pdf, (pdf.epw / 2, pdf.eph / 4), "EAST")
        pdf.cell(text="cell text 1", fill=True)
        pdf.ln(40)

    pdf.cell(text="cell text 2")
    pdf.x = pdf.l_margin
    with pdf.mirror((pdf.epw / 2, 0), "SOUTHWEST"):
        draw_mirror_line(pdf, (pdf.epw / 2, 0), "SOUTHWEST")
        pdf.cell(text="cell text 2", fill=True)
        pdf.ln(40)

    pdf.cell(text="cell text 3")
    pdf.x = pdf.l_margin
    with pdf.mirror((pdf.epw / 2, pdf.eph / 4), "NORTHEAST"):
        draw_mirror_line(pdf, (pdf.epw / 2, pdf.eph / 4), "NORTHEAST")
        pdf.cell(text="cell text 3", fill=True, border=1)
        pdf.ln(40)

    assert_pdf_equal(pdf, HERE / "mirror_cell.pdf", tmp_path)


def test_mirror_multi_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.set_fill_color(255, 255, 0)

    pdf.multi_cell(w=50, text=LOREM_IPSUM[:200])

    pdf.x = pdf.l_margin
    pdf.y = pdf.t_margin
    with pdf.mirror((pdf.epw / 2, pdf.eph / 4), "NORTHEAST"):
        draw_mirror_line(pdf, (pdf.epw / 2, pdf.eph / 4), "NORTHEAST")
        pdf.multi_cell(w=50, text=LOREM_IPSUM[:200], fill=True)
        pdf.ln(20)

    prev_y = pdf.y
    pdf.multi_cell(w=100, text=LOREM_IPSUM[:200])
    pdf.x = pdf.l_margin
    pdf.y = prev_y

    with pdf.mirror((0, pdf.eph / 2), "EAST"):
        draw_mirror_line(pdf, (0, pdf.eph / 2), "EAST")
        pdf.multi_cell(w=100, text=LOREM_IPSUM[:200], fill=True)
        pdf.ln(150)

    prev_y = pdf.y
    pdf.multi_cell(w=120, text=LOREM_IPSUM[:120])
    pdf.x = pdf.l_margin
    pdf.y = prev_y

    with pdf.mirror((pdf.epw / 2, pdf.eph), "SOUTH"):
        draw_mirror_line(pdf, (pdf.epw / 2, pdf.eph), "SOUTH")
        pdf.multi_cell(w=120, text=LOREM_IPSUM[:120], fill=True, border=1)

    assert_pdf_equal(pdf, HERE / "mirror_multi_cell.pdf", tmp_path)
