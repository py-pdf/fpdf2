# test/test_text_rendering.py
import math
from pathlib import Path
import pytest
from fpdf import FPDF
from fpdf.drawing import GradientPaint, GraphicsContext, PaintedPath
from fpdf.drawing_primitives import DeviceRGB, Transform
from fpdf.drawing import Text
from fpdf.pattern import LinearGradient
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def _new_pdf():
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_page()
    return pdf


def _rect(x, y, w, h):
    return PaintedPath().rectangle(x, y, w, h)


def test_text_and_shape_order(tmp_path: Path):
    pdf = _new_pdf()

    gc = GraphicsContext()

    # Text first
    t = Text(
        x=40,
        y=80,
        text="Hello Overlap",
        font_family="helvetica",
        font_style="",
        font_size=24,
        text_anchor="start",
    )
    gc.add_item(t)

    # Opaque rectangle drawn AFTER text (covers part of it)
    r = _rect(60, 55, 120, 30)
    r.style.fill_color = "#FF0000"
    r.style.stroke_color = "#000000"
    r.style.stroke_width = 0.5
    gc.add_item(r)

    with pdf.drawing_context() as dc:
        dc.add_item(gc)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "text_shape_order.pdf", tmp_path)


def test_shape_with_transparency_over_text(tmp_path: Path):
    pdf = _new_pdf()

    gc = GraphicsContext()

    # Text baseline
    t = Text(
        x=40,
        y=130,
        text="Transparent Shape Over Me",
        font_family="helvetica",
        font_style="",
        font_size=26,
    )
    gc.add_item(t)

    # Semi-transparent blue rectangle over the text
    rect = _rect(35, 105, 260, 32)
    rect.style.fill_color = DeviceRGB(r=0, g=0, b=1, a=0.35)
    rect.style.stroke_color = None
    gc.add_item(rect)

    with pdf.drawing_context() as dc:
        dc.add_item(gc)

    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "shape_alpha_over_text.pdf", tmp_path
    )


def test_text_with_transparency_over_shape(tmp_path: Path):
    pdf = _new_pdf()

    root = GraphicsContext()

    # Background shape (opaque)
    bg = _rect(30, 180, 310, 50)
    bg.style.fill_color = "#EEEEEE"
    bg.style.stroke_color = "#000000"
    bg.style.stroke_width = 0.5
    root.add_item(bg)

    # Child GC that carries alpha in its style for the text fill
    gc_text = GraphicsContext()
    gc_text.style.fill_color = DeviceRGB(r=0, g=0, b=0, a=0.4)

    t = Text(
        x=40,
        y=210,
        text="Semi-Transparent Text",
        font_family="helvetica",
        font_style="",
        font_size=28,
    )
    gc_text.add_item(t)
    root.add_item(gc_text)

    with pdf.drawing_context() as dc:
        dc.add_item(root)

    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "text_alpha_over_shape.pdf", tmp_path
    )


def test_text_gradient_transparency(tmp_path: Path):
    pdf = _new_pdf()

    square = PaintedPath()
    square.rectangle(30, 250, 250, 50)
    square.style.fill_color = "#000000"

    gradient = LinearGradient(
        from_x=30, from_y=0, to_x=280, to_y=0, colors=["#ff0000", "#ffff00"]
    )
    text = PaintedPath()
    text.add_path_element(
        Text(
            x=40,
            y=280,
            text="Gradient Text Fill",
            font_family="helvetica",
            font_style="",
            font_size=30,
        )
    )
    text.style.fill_color = GradientPaint(gradient, units="userSpaceOnUse")

    with pdf.drawing_context() as dc:
        dc.add_item(square)
        dc.add_item(text)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "text_fill_gradient.pdf", tmp_path)


def test_text_fonts_styles_alignment(tmp_path: Path):
    pdf = _new_pdf()

    root = GraphicsContext()

    x = 300  # common anchor for alignment tests

    # Visual guide line
    guide = PaintedPath().move_to(x, 20).line_to(x, 320)
    guide.style.stroke_color = "#00AA00"
    guide.style.stroke_width = 0.4
    root.add_item(guide)

    items = [
        Text(
            x=x,
            y=80,
            text="Start / Helvetica",
            font_family="DejaVu, sans-serif",
            font_style="",
            font_size=20,
            text_anchor="start",
        ),
        Text(
            x=x,
            y=110,
            text="Middle / Helvetica B",
            font_family="non-existent, helvetica",
            font_style="B",
            font_size=20,
            text_anchor="middle",
        ),
        Text(
            x=x,
            y=140,
            text="End / Helvetica I",
            font_family="helvetica",
            font_style="I",
            font_size=20,
            text_anchor="end",
        ),
        Text(
            x=x,
            y=170,
            text="Start / Times BI",
            font_family="times",
            font_style="BI",
            font_size=20,
            text_anchor="start",
        ),
        Text(
            x=x,
            y=200,
            text="Middle / Courier",
            font_family="courier",
            font_style="",
            font_size=20,
            text_anchor="middle",
        ),
        Text(
            x=x,
            y=230,
            text="End / Courier B",
            font_family="courier",
            font_style="B",
            font_size=20,
            text_anchor="end",
        ),
    ]
    for it in items:
        root.add_item(it)

    with pdf.drawing_context() as dc:
        dc.add_item(root)

    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "text_fonts_styles_alignment.pdf", tmp_path
    )


def test_text_font_not_found_raises():
    pdf = _new_pdf()

    gc = GraphicsContext()

    t = Text(
        x=50,
        y=320,
        text="Should fail to resolve font",
        font_family="__no_such_font_family__",
        font_style="",
        font_size=18,
    )
    gc.add_item(t)

    with pytest.raises(KeyError) as err:
        with pdf.drawing_context() as dc:
            dc.add_item(gc)
    assert "No suitable font for family='__no_such_font_family__'" in str(err.value)


def test_text_ttf_transforms(tmp_path: Path):
    pdf = _new_pdf()

    pdf.add_font(
        family="DejaVu",
        fname=HERE.parent / "fonts" / "DejaVuSans.ttf",
    )
    pdf.add_font(
        family="NotoEmoji",
        fname=HERE.parent / "color_font" / "colrv1-NotoColorEmoji.ttf",
    )

    root = GraphicsContext()

    # Untransformed guide & DejaVu lines (baseline reference)
    x = 300
    guide = PaintedPath().move_to(x, 30).line_to(x, 330)
    guide.style.stroke_color = "#808080"
    guide.style.stroke_width = 0.4
    root.add_item(guide)

    root.add_item(
        Text(
            x=x,
            y=70,
            text="Start / DejaVu",
            font_family="DejaVu",
            font_style="",
            font_size=20,
            text_anchor="start",
        )
    )
    root.add_item(
        Text(
            x=x,
            y=100,
            text="Middle / DejaVu",
            font_family="DejaVu",
            font_style="",
            font_size=20,
            text_anchor="middle",
        )
    )
    root.add_item(
        Text(
            x=x,
            y=130,
            text="End / DejaVu",
            font_family="DejaVu",
            font_style="",
            font_size=20,
            text_anchor="end",
        )
    )

    # A rotated/translated child GC to test transforms with text anchors
    # Rotate around (x, 220) by -25 degrees
    gc_rot = GraphicsContext()
    gc_rot.transform = Transform.rotation(math.radians(-25)).about(x, 220)

    # A green guide line inside the rotated GC (to visualize the new anchor line)
    guide_rot = PaintedPath().move_to(x, 160).line_to(x, 280)
    guide_rot.style.stroke_color = "#00AA00"
    guide_rot.style.stroke_width = 0.4
    gc_rot.add_item(guide_rot)

    # DejaVu under transform (anchors should align on the rotated green guide)
    gc_rot.add_item(
        Text(
            x=x,
            y=190,
            text="Start / DejaVu (rot)",
            font_family="dejavu, helvetica, sans serif",
            font_style="",
            font_size=18,
            text_anchor="start",
        )
    )
    gc_rot.add_item(
        Text(
            x=x,
            y=220,
            text="Middle / DejaVu (rot)",
            font_family="DejaVu",
            font_style="",
            font_size=18,
            text_anchor="middle",
        )
    )
    gc_rot.add_item(
        Text(
            x=x,
            y=250,
            text="End / DejaVu (rot)",
            font_family="DEJAVU",
            font_style="",
            font_size=18,
            text_anchor="end",
        )
    )

    # NotoEmoji sample (TTF shaping/encoding path) – not rotated
    root.add_item(
        Text(
            x=40,
            y=310,
            text="😀🚀☕",
            font_family="NotoEmoji",
            font_style="",
            font_size=28,
        )
    )

    root.add_item(gc_rot)

    with pdf.drawing_context() as dc:
        dc.add_item(root)

    assert_pdf_equal(pdf, HERE / "generated_pdf" / "text_ttf_transforms.pdf", tmp_path)
