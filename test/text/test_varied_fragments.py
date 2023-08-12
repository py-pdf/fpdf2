""" Test that _render_styled_text_line() correctly handles sequences of
Fragments with varying font/size/style and other characteristics.
"""

# pylint: disable=protected-access
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos
from fpdf.line_break import Fragment, MultiLineBreak
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


TEXT_1 = "Lorem ipsum Ut nostrud irure"
TEXT_2 = " reprehenderit anim nostrud dolore sed ut Excepteur dolore ut"
TEXT_3 = " sunt irure consectetur tempor eu tempor nostrud dolore sint"
TEXT_4 = " exercitation aliquip velit ullamco esse dolore mollit"
TEXT_5 = " ea sed voluptate commodo amet eiusmod incididunt"


class FxFPDF(FPDF):
    def write_fragments(self, frags, align=Align.L):
        """Replicate the part of write() that actually renders the fragments."""
        def _get_width(height):  # pylint: disable=unused-argument
            return max_width
        text_lines = []
        justify = align == Align.J
        multi_line_break = MultiLineBreak(frags, _get_width, justify=justify)
        # first line from current x position to right margin
        first_width = self.w - self.x - self.r_margin
        max_width = first_width - 2 * self.c_margin
        text_line = multi_line_break.get_line()
        # remaining lines fill between margins
        full_width = self.w - self.l_margin - self.r_margin
        max_width = full_width - 2 * self.c_margin
        while (text_line) is not None:
            text_lines.append(text_line)
            text_line = multi_line_break.get_line()
        if text_line:
            text_lines.append(text_line)
        if not text_lines:
            return
        self.ws = 0  # currently only left aligned, so no word spacing
        for text_line_index, text_line in enumerate(text_lines):
            if text_line_index == 0:
                line_width = first_width
            else:
                line_width = full_width
                self.ln()
            is_last_line = text_line_index == len(text_lines) - 1
            self._render_styled_text_line(
                text_line,
                line_width,
                h=None,
                border=0,
                new_x=XPos.WCONT,
                new_y=YPos.TOP,
                align=Align.L if (align == Align.J and is_last_line) else align,
                fill=False,
                link=None,
            )


def test_varfrags_fonts(tmp_path):
    pdf = FxFPDF()
    pdf.add_page()
    pdf.line(pdf.l_margin, pdf.t_margin, pdf.l_margin, pdf.h - pdf.b_margin)
    pdf.line(
        pdf.l_margin + pdf.epw,
        pdf.t_margin,
        pdf.l_margin + pdf.epw,
        pdf.h - pdf.b_margin,
    )
    pdf.add_font("Roboto", "B", HERE / "../fonts/Roboto-Bold.ttf")
    pdf.set_font("helvetica", "", 14)
    f1 = Fragment(TEXT_1, pdf._get_current_graphics_state(), pdf.k)
    pdf.set_font("courier", "I", 16)
    f2 = Fragment(TEXT_2, pdf._get_current_graphics_state(), pdf.k)
    f3 = Fragment(TEXT_3, f1.graphics_state, pdf.k)
    pdf.set_font("roboto", "B", 20)
    f4 = Fragment(TEXT_4, pdf._get_current_graphics_state(), pdf.k)
    f5 = Fragment(TEXT_5, f1.graphics_state, pdf.k)
    frags = [f1, f2, f3, f4, f5]
    pdf.write_fragments(frags)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.J)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.R)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.C)
    assert_pdf_equal(pdf, HERE / "varfrags_fonts.pdf", tmp_path)


def test_varfrags_size_bold(tmp_path):
    pdf = FxFPDF()
    pdf.add_page()
    pdf.line(pdf.l_margin, pdf.t_margin, pdf.l_margin, pdf.h - pdf.b_margin)
    pdf.line(
        pdf.l_margin + pdf.epw,
        pdf.t_margin,
        pdf.l_margin + pdf.epw,
        pdf.h - pdf.b_margin,
    )
    pdf.set_font("helvetica", "", 14)
    f1 = Fragment(TEXT_1, pdf._get_current_graphics_state(), pdf.k)
    pdf.set_font("helvetica", "B", 30)
    f2 = Fragment(TEXT_2, pdf._get_current_graphics_state(), pdf.k)
    f3 = Fragment(TEXT_3, f1.graphics_state, pdf.k)
    f4 = Fragment(TEXT_4, f2.graphics_state, pdf.k)
    f5 = Fragment(TEXT_5, f1.graphics_state, pdf.k)
    frags = [f1, f2, f3, f4, f5]
    pdf.write_fragments(frags)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.J)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.R)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.C)
    assert_pdf_equal(pdf, HERE / "varfrags_size_bold.pdf", tmp_path)


def test_varfrags_stretch_spacing(tmp_path):
    pdf = FxFPDF()
    pdf.add_page()
    pdf.line(pdf.l_margin, pdf.t_margin, pdf.l_margin, pdf.h - pdf.b_margin)
    pdf.line(
        pdf.l_margin + pdf.epw,
        pdf.t_margin,
        pdf.l_margin + pdf.epw,
        pdf.h - pdf.b_margin,
    )
    pdf.set_font("helvetica", "", 14)
    f1 = Fragment(TEXT_1, pdf._get_current_graphics_state(), pdf.k)
    pdf.set_stretching(140)
    f2 = Fragment(TEXT_2, pdf._get_current_graphics_state(), pdf.k)
    f3 = Fragment(TEXT_3, f1.graphics_state, pdf.k)
    pdf.set_char_spacing(-3)
    f4 = Fragment(TEXT_4, pdf._get_current_graphics_state(), pdf.k)
    f5 = Fragment(TEXT_5, f1.graphics_state, pdf.k)
    frags = [f1, f2, f3, f4, f5]
    pdf.write_fragments(frags)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.J)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.R)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.C)
    assert_pdf_equal(pdf, HERE / "varfrags_stretch_spacing.pdf", tmp_path)


def test_varfrags_text_mode(tmp_path):
    pdf = FxFPDF()
    pdf.add_page()
    pdf.line(pdf.l_margin, pdf.t_margin, pdf.l_margin, pdf.h - pdf.b_margin)
    pdf.line(
        pdf.l_margin + pdf.epw,
        pdf.t_margin,
        pdf.l_margin + pdf.epw,
        pdf.h - pdf.b_margin,
    )
    pdf.set_draw_color(255, 100, 0)
    pdf.line_width = 1
    pdf.set_font("helvetica", "B", 20)
    f1 = Fragment(TEXT_1, pdf._get_current_graphics_state(), pdf.k)
    pdf.text_mode = "STROKE"
    f2 = Fragment(TEXT_2, pdf._get_current_graphics_state(), pdf.k)
    f3 = Fragment(TEXT_3, f1.graphics_state, pdf.k)
    # For now, the most recently set color before write_fragments() wins.
    pdf.set_draw_color(0, 0, 255)
    pdf.text_mode = "FILL_STROKE"
    f4 = Fragment(TEXT_4, pdf._get_current_graphics_state(), pdf.k)
    f5 = Fragment(TEXT_5, f1.graphics_state, pdf.k)
    frags = [f1, f2, f3, f4, f5]
    pdf.write_fragments(frags)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.J)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.R)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.C)
    assert_pdf_equal(pdf, HERE / "varfrags_text_mode.pdf", tmp_path)


def test_varfrags_char_vpos(tmp_path):
    pdf = FxFPDF()
    pdf.add_page()
    pdf.line(pdf.l_margin, pdf.t_margin, pdf.l_margin, pdf.h - pdf.b_margin)
    pdf.line(
        pdf.l_margin + pdf.epw,
        pdf.t_margin,
        pdf.l_margin + pdf.epw,
        pdf.h - pdf.b_margin,
    )
    pdf.set_font("helvetica", "", 14)
    f1 = Fragment(TEXT_1, pdf._get_current_graphics_state(), pdf.k)
    pdf.char_vpos = "SUB"
    f2 = Fragment(TEXT_2, pdf._get_current_graphics_state(), pdf.k)
    f3 = Fragment(TEXT_3, f1.graphics_state, pdf.k)
    pdf.char_vpos = "SUP"
    f4 = Fragment(TEXT_4, pdf._get_current_graphics_state(), pdf.k)
    f5 = Fragment(TEXT_5, f1.graphics_state, pdf.k)
    frags = [f1, f2, f3, f4, f5]
    pdf.write_fragments(frags)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.J)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.R)
    pdf.ln()
    pdf.ln()
    pdf.write_fragments(frags, align=Align.C)
    assert_pdf_equal(pdf, HERE / "varfrags_char_vpos.pdf", tmp_path)
