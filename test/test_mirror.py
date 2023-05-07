import math
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import Angle
from test.conftest import assert_pdf_equal, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def draw_mirror_line(pdf, angle, origin=(None, None)):
    """
    A helper method which converts a given angle and origin to two co-ordinates to
    then draw a line.
    Used to help visualize & test mirror transformations.

    Args:
        pdf (fpdf.FPDF): pdf to modify
        angle: (fpdf.enums.Angle): the direction of the mirror line
        origin (Sequence[float, float]): a point on the mirror line
    """

    angle = Angle.coerce(angle)

    x, y = origin
    if x is None:
        x = pdf.x
    if y is None:
        y = pdf.y

    theta = angle.value

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
    with pdf.mirror("WEST", (pdf.epw / 2, pdf.eph / 2.5)):
        draw_mirror_line(pdf, "WEST", (pdf.epw / 2, pdf.eph / 2.5))
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror("SOUTH", (pdf.epw / 2.5, pdf.eph / 2)):
        pdf.set_draw_color(r=128, g=0, b=0)
        draw_mirror_line(pdf, "SOUTH", (pdf.epw / 2.5, pdf.eph / 2))
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror("SOUTHWEST", (pdf.epw / 1.5, pdf.eph / 1.5)):
        pdf.set_draw_color(r=0, g=0, b=128)
        draw_mirror_line(pdf, "SOUTHWEST", (pdf.epw / 1.5, pdf.eph / 1.5))
        pdf.image(img_filepath, x=100, y=100)

    with pdf.mirror("SOUTHEAST", (pdf.epw / 3, pdf.eph / 2.5)):
        pdf.set_draw_color(r=0, g=128, b=0)
        draw_mirror_line(pdf, "SOUTHEAST", (pdf.epw / 3, pdf.eph / 2.5))
        pdf.image(img_filepath, x=100, y=100)

    assert_pdf_equal(pdf, HERE / "mirror.pdf", tmp_path)


def test_mirror_text(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    pdf.text(pdf.epw / 2, pdf.epw / 2, txt="mirror this text")

    with pdf.mirror("EAST", (pdf.epw / 2, pdf.eph / 2.5)):
        pdf.text(pdf.epw / 2, pdf.eph / 2, txt="mirrored text E/W")

    with pdf.mirror("NORTH", (pdf.epw / 2.5, pdf.eph / 2)):
        pdf.text(pdf.epw / 2, pdf.eph / 2, txt="mirrored text N/S")

    with pdf.mirror("NORTHWEST", (pdf.epw / 1.5, pdf.eph / 1.5)):
        pdf.text(pdf.epw / 2, pdf.eph / 2, txt="mirrored text NW/SE")

    with pdf.mirror("NORTHEAST", (pdf.epw / 2.5, pdf.eph / 2.5)):
        pdf.text(pdf.epw / 2, pdf.eph / 2, txt="mirrored text NE/SW")

    assert_pdf_equal(pdf, HERE / "mirror_text.pdf", tmp_path)


def test_mirror_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.set_fill_color(255, 255, 0)

    pdf.cell(txt="cell to be mirrored repeatedly")
    pdf.x = pdf.l_margin
    with pdf.mirror("NORTH", (pdf.epw / 2, 0)):
        draw_mirror_line(pdf, "NORTH", (pdf.epw / 2, 0))
        pdf.cell(txt="cell mirrored", fill=True)
        pdf.cell(txt="cell mirrored", fill=True)
        pdf.cell(txt="cell mirrored", fill=True)
        pdf.ln(40)

    pdf.cell(txt="cell text 1")
    pdf.x = pdf.l_margin
    with pdf.mirror("EAST", (pdf.epw / 2, pdf.eph / 4)):
        draw_mirror_line(pdf, "EAST", (pdf.epw / 2, pdf.eph / 4))
        pdf.cell(txt="cell text 1", fill=True)
        pdf.ln(40)

    pdf.cell(txt="cell text 2")
    pdf.x = pdf.l_margin
    with pdf.mirror("SOUTHWEST", (pdf.epw / 2, 0)):
        draw_mirror_line(pdf, "SOUTHWEST", (pdf.epw / 2, 0))
        pdf.cell(txt="cell text 2", fill=True)
        pdf.ln(40)

    pdf.cell(txt="cell text 3")
    pdf.x = pdf.l_margin
    with pdf.mirror("NORTHEAST", (pdf.epw / 2, pdf.eph / 4)):
        draw_mirror_line(pdf, "NORTHEAST", (pdf.epw / 2, pdf.eph / 4))
        pdf.cell(txt="cell text 3", fill=True)
        pdf.ln(40)

    assert_pdf_equal(pdf, HERE / "mirror_cell.pdf", tmp_path)


def test_mirror_multi_cell(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.set_fill_color(255, 255, 0)

    pdf.multi_cell(w=50, txt=LOREM_IPSUM[:200])

    pdf.x = pdf.l_margin
    pdf.y = pdf.t_margin
    with pdf.mirror("NORTHEAST", (pdf.epw / 2, pdf.eph / 4)):
        draw_mirror_line(pdf, "NORTHEAST", (pdf.epw / 2, pdf.eph / 4))
        pdf.multi_cell(w=50, txt=LOREM_IPSUM[:200], fill=True)
        pdf.ln(20)

    prev_y = pdf.y
    pdf.multi_cell(w=100, txt=LOREM_IPSUM[:200])
    pdf.x = pdf.l_margin
    pdf.y = prev_y

    with pdf.mirror("EAST", (0, pdf.eph / 2)):
        draw_mirror_line(pdf, "EAST", (0, pdf.eph / 2))
        pdf.multi_cell(w=100, txt=LOREM_IPSUM[:200], fill=True)
        pdf.ln(150)

    prev_y = pdf.y
    pdf.multi_cell(w=120, txt=LOREM_IPSUM[:120])
    pdf.x = pdf.l_margin
    pdf.y = prev_y

    with pdf.mirror("SOUTH", (pdf.epw / 2, pdf.eph)):
        draw_mirror_line(pdf, "SOUTH", (pdf.epw / 2, pdf.eph))
        pdf.multi_cell(w=120, txt=LOREM_IPSUM[:120], fill=True)

    pdf.output(HERE / "mirror_multi_cell.pdf")
    assert_pdf_equal(
        pdf,
        HERE / "mirror_multi_cell.pdf",
        tmp_path,
    )
