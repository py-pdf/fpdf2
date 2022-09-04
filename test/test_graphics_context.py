from pathlib import Path

import pytest

from fpdf import FPDF, drawing
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_graphics_context(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0x00, 0xFF, 0x00)
    pdf.set_fill_color(0xFF, 0x88, 0xFF)
    pdf.set_y(20)
    pdf.cell(txt="outer 01", new_x="LMARGIN", new_y="NEXT", fill=True)
    with pdf.local_context():
        pdf.set_font("courier", "BIU", 30)
        pdf.set_text_color(0xFF, 0x00, 0x00)
        pdf.set_fill_color(0xFF, 0xFF, 0x00)
        pdf.cell(txt="inner 01", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_x(70)
        with pdf.rotation(30, pdf.get_x(), pdf.get_y()):
            pdf.set_fill_color(0x00, 0xFF, 0x00)
            pdf.cell(txt="inner 02", new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_stretching(150)
        pdf.cell(txt="inner 03", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.cell(txt="outer 02", new_x="LMARGIN", new_y="NEXT", fill=True)
    assert_pdf_equal(pdf, HERE / "graphics_context.pdf", tmp_path)


def test_change_settings():
    """
    Make sure all the the set_xxx() methods stored in the graphics context
    do the right thing, both when changing something or using the same value
    again (the latter will often execute a seperate, shortened code path).
    """
    red = (255, 0, 0)
    blue = (0, 255, 0)
    green = (0, 0, 255)

    # draw color
    pdf = FPDF()
    # verify default
    tgt_draw_color = pdf.DEFAULT_DRAW_COLOR
    assert (
        pdf.draw_color == tgt_draw_color
    ), f"pdf.draw_color ({pdf.draw_color}) != tgt_draw_color ({tgt_draw_color})"
    # change to red
    tgt_draw_color = drawing.DeviceRGB(*[c / 255 for c in red])
    pdf.set_draw_color(*red)
    assert (
        pdf.draw_color == tgt_draw_color
    ), f"pdf.draw_color ({pdf.draw_color}) != tgt_draw_color ({tgt_draw_color})"
    # stays the same
    pdf.set_draw_color(*red)
    assert (
        pdf.draw_color == tgt_draw_color
    ), f"pdf.draw_color ({pdf.draw_color}) != tgt_draw_color ({tgt_draw_color})"

    # fill color
    pdf = FPDF()
    # verify default
    tgt_fill_color = pdf.DEFAULT_FILL_COLOR
    assert (
        pdf.fill_color == tgt_fill_color
    ), f"pdf.fill_color ({pdf.fill_color}) != tgt_fill_color ({tgt_fill_color})"
    # change to green
    tgt_fill_color = drawing.DeviceRGB(*[c / 255 for c in green])
    pdf.set_fill_color(*green)
    assert (
        pdf.fill_color == tgt_fill_color
    ), f"pdf.fill_color ({pdf.fill_color}) != tgt_fill_color ({tgt_fill_color})"
    # stays the same
    pdf.set_fill_color(*green)
    assert (
        pdf.fill_color == tgt_fill_color
    ), f"pdf.fill_color ({pdf.fill_color}) != tgt_fill_color ({tgt_fill_color})"

    # text color
    pdf = FPDF()
    # verify default
    tgt_text_color = pdf.DEFAULT_TEXT_COLOR
    assert (
        pdf.text_color == tgt_text_color
    ), f"pdf.text_color ({pdf.text_color}) != tgt_text_color ({tgt_text_color})"
    # change to blue
    tgt_text_color = drawing.DeviceRGB(*[c / 255 for c in blue])
    pdf.set_text_color(*blue)
    assert (
        pdf.text_color == tgt_text_color
    ), f"pdf.text_color ({pdf.text_color}) != tgt_text_color ({tgt_text_color})"
    # stays the same
    pdf.set_text_color(*blue)
    assert (
        pdf.text_color == tgt_text_color
    ), f"pdf.text_color ({pdf.text_color}) != tgt_text_color ({tgt_text_color})"

    # underline
    # no setter method for this one

    # font_stretching
    pdf = FPDF()
    # verify default
    tgt_font_stretching = 100
    assert pdf.font_stretching == tgt_font_stretching, (
        f"pdf.font_stretching ({pdf.font_stretching})"
        f" != tgt_font_stretching ({tgt_font_stretching})"
    )
    # change
    tgt_font_stretching = 120
    pdf.set_stretching(tgt_font_stretching)
    assert pdf.font_stretching == tgt_font_stretching, (
        f"pdf.font_stretching ({pdf.font_stretching})"
        f" != tgt_font_stretching ({tgt_font_stretching})"
    )
    # stays the same
    pdf.set_stretching(tgt_font_stretching)
    assert pdf.font_stretching == tgt_font_stretching, (
        f"pdf.font_stretching ({pdf.font_stretching})"
        f" != tgt_font_stretching ({tgt_font_stretching})"
    )

    # char_spacing
    pdf = FPDF()
    # verify default
    tgt_char_spacing = 0
    assert pdf.char_spacing == tgt_char_spacing, (
        f"pdf.char_spacing ({pdf.char_spacing})"
        f" != tgt_char_spacing ({tgt_char_spacing})"
    )
    # change
    tgt_char_spacing = 5
    pdf.set_char_spacing(tgt_char_spacing)
    assert pdf.char_spacing == tgt_char_spacing, (
        f"pdf.char_spacing ({pdf.char_spacing})"
        f" != tgt_char_spacing ({tgt_char_spacing})"
    )
    # stays the same
    pdf.set_char_spacing(tgt_char_spacing)
    assert pdf.char_spacing == tgt_char_spacing, (
        f"pdf.char_spacing ({pdf.char_spacing})"
        f" != tgt_char_spacing ({tgt_char_spacing})"
    )

    # dash_pattern
    pdf = FPDF()
    # verify default
    tgt_dash_pattern = dict(dash=0, gap=0, phase=0)
    assert pdf.dash_pattern == tgt_dash_pattern, (
        f"pdf.dash_pattern ({pdf.dash_pattern})"
        f" != tgt_dash_pattern ({tgt_dash_pattern})"
    )
    # change
    tgt_dash_pattern = dict(dash=2, gap=1, phase=0)
    pdf.set_dash_pattern(**tgt_dash_pattern)
    assert pdf.dash_pattern == tgt_dash_pattern, (
        f"pdf.dash_pattern ({pdf.dash_pattern})"
        f" != tgt_dash_pattern ({tgt_dash_pattern})"
    )
    # stays the same
    pdf.set_dash_pattern(**tgt_dash_pattern)
    assert pdf.dash_pattern == tgt_dash_pattern, (
        f"pdf.dash_pattern ({pdf.dash_pattern})"
        f" != tgt_dash_pattern ({tgt_dash_pattern})"
    )

    # line_width
    pdf = FPDF()
    # verify default
    tgt_line_width = 0.567 / pdf.k
    assert (
        pdf.line_width == tgt_line_width
    ), f"pdf.line_width ({pdf.line_width}) != tgt_line_width ({tgt_line_width})"
    # change
    tgt_line_width = 0.5
    pdf.set_line_width(tgt_line_width)
    assert (
        pdf.line_width == tgt_line_width
    ), f"pdf.line_width ({pdf.line_width}) != tgt_line_width ({tgt_line_width})"
    # stays the same
    pdf.set_line_width(tgt_line_width)
    assert (
        pdf.line_width == tgt_line_width
    ), f"pdf.line_width ({pdf.line_width}) != tgt_line_width ({tgt_line_width})"

    # text_mode
    # no setter method for this one

    # font_size_pt
    pdf = FPDF()
    # verify default
    tgt_font_size_pt = 12
    tgt_font_size = tgt_font_size_pt / pdf.k
    assert pdf.font_size_pt == tgt_font_size_pt, (
        f"pdf.font_size_pt ({pdf.font_size_pt})"
        f" != tgt_font_size_pt ({tgt_font_size_pt})"
    )
    assert (
        pdf.font_size == tgt_font_size
    ), f"pdf.font_size ({pdf.font_size}) != tgt_font_size ({tgt_font_size})"
    # change
    tgt_font_size_pt = 14
    tgt_font_size = tgt_font_size_pt / pdf.k
    pdf.set_font_size(tgt_font_size_pt)
    assert pdf.font_size_pt == tgt_font_size_pt, (
        f"pdf.font_size_pt ({pdf.font_size_pt})"
        f" != tgt_font_size_pt ({tgt_font_size_pt})"
    )
    assert (
        pdf.font_size == tgt_font_size
    ), f"pdf.font_size ({pdf.font_size}) != tgt_font_size ({tgt_font_size})"
    # stays the same
    pdf.set_font_size(tgt_font_size_pt)
    assert pdf.font_size_pt == tgt_font_size_pt, (
        f"pdf.font_size_pt ({pdf.font_size_pt})"
        f" != tgt_font_size_pt ({tgt_font_size_pt})"
    )
    assert (
        pdf.font_size == tgt_font_size
    ), f"pdf.font_size ({pdf.font_size}) != tgt_font_size ({tgt_font_size})"

    # font
    pdf = FPDF()
    # verify default
    tgt_font = ("", "", 12)
    assert (
        pdf.font_family == tgt_font[0]
    ), f"pdf.font_family ({pdf.font_family}) != tgt_font[0] ({tgt_font[0]})"
    assert (
        pdf.font_style == tgt_font[1]
    ), f"pdf.font_style ({pdf.font_style}) != tgt_font[1] ({tgt_font[1]})"
    assert (
        pdf.font_size_pt == tgt_font[2]
    ), f"pdf.font_size_pt ({pdf.font_size_pt}) != tgt_font[2] ({tgt_font[2]})"
    # change
    for tgt_font in (
        dict(family="helvetica"),
        dict(family="helvetica", style="B"),
        dict(family="helvetica", size=14),
        dict(family="helvetica", style="I", size=12),
    ):
        pdf = FPDF()
        pdf.set_font(**tgt_font)
        assert pdf.font_family == tgt_font.get("family", ""), (
            f"pdf.font_family ({pdf.font_family})"
            f" != tgt_font.get('family', '') ({tgt_font.get('family', '')})"
        )
        assert pdf.font_style == tgt_font.get("style", ""), (
            f"pdf.font_style ({pdf.font_style})"
            f" != tgt_font.get('style', '') ({tgt_font.get('style', '')})"
        )
        assert pdf.font_size_pt == tgt_font.get("size", 12), (
            f"pdf.font_size_pt ({pdf.font_size_pt})"
            f" != tgt_font.get('size', 12) ({tgt_font.get('size', 12)})"
        )
    # stays the same
    pdf.set_font(**tgt_font)
    assert pdf.font_family == tgt_font.get("family"), (
        f"pdf.font_family ({pdf.font_family})"
        f" != tgt_font.get('family', '') ({tgt_font.get('family', '')})"
    )
    assert pdf.font_style == tgt_font.get("style"), (
        f"pdf.font_style ({pdf.font_style})"
        f" != tgt_font.get('style', '') ({tgt_font.get('style', '')})"
    )
    assert pdf.font_size_pt == tgt_font.get("size"), (
        f"pdf.font_size_pt ({pdf.font_size_pt})"
        f" != tgt_font.get('size', 12) ({tgt_font.get('size', 12)})"
    )


def test_local_context_init(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    with pdf.local_context(
        font_family="Courier", font_style="B", font_size=24, text_color=(255, 128, 0)
    ):
        pdf.cell(txt="Local context")
    pdf.ln()
    pdf.cell(txt="Back to base")
    assert_pdf_equal(pdf, HERE / "local_context_init.pdf", tmp_path)


def test_local_context_shared_props(tmp_path):
    "Test local_context() with settings that are controlled by both GraphicsStateMixin and drawing.GraphicsStyle"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    with pdf.local_context(
        draw_color=(0, 128, 255),
        fill_color=(255, 128, 0),
        line_width=2,
        dash_pattern=dict(dash=0.5, gap=9.5, phase=3.25),
    ):
        pdf.rect(x=60, y=60, w=60, h=60, style="DF")
    pdf.rect(x=60, y=150, w=60, h=60, style="DF")
    assert_pdf_equal(pdf, HERE / "local_context_shared_props.pdf", tmp_path)


def test_local_context_inherited_shared_props(tmp_path):
    "The only thing that should differ between the 2 squares is their opacity"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    pdf.set_draw_color(0, 128, 255)
    pdf.set_fill_color(255, 128, 0)
    pdf.set_line_width(2)
    pdf.set_dash_pattern(dash=0.5, gap=9.5, phase=3.25)
    with pdf.local_context(
        fill_opacity=0.5
    ):  # => triggers creation of a local GraphicsStyle
        pdf.rect(x=60, y=60, w=60, h=60, style="DF")
    pdf.rect(x=60, y=150, w=60, h=60, style="DF")
    assert_pdf_equal(pdf, HERE / "local_context_inherited_shared_props.pdf", tmp_path)


def test_invalid_local_context_init():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        with pdf.local_context(font_size_pt=24):
            pass
    with pytest.raises(ValueError):
        with pdf.local_context(stroke_width=2):
            pass
