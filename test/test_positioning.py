""" Tests related to positioning self.x and self.y on the page.
    implemented:
    * ln()
    to be implemented:
    * set_x()
    * set_y()
    * set_xy()
"""
from pathlib import Path
import math

import pytest

from fpdf import FPDF

# from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

# pylint: disable=protected-access


def test_ln_before_text():  # Issue 937
    pdf = FPDF()
    pdf.add_page()

    # no text added yet, ln() uses default font_size
    pdf.x += 20
    prev_y = pdf.y
    pdf.ln()
    assert math.isclose(
        pdf.y - prev_y, pdf.font_size
    ), f"ln() before writing text didn't move y by font size ({pdf.y-prev_y} vs. {pdf.font_size})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() before writing text didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."

    # changed font size affects amount of movement
    pdf.set_font("helvetica", size=36)
    pdf.x += 30
    prev_y = pdf.y
    pdf.ln()
    assert math.isclose(
        pdf.y - prev_y, pdf.font_size
    ), f"ln() before writing text didn't move y by font size ({pdf.y-prev_y} vs. {pdf.font_size})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() before writing text didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."


def test_ln_by_h():
    pdf = FPDF()
    pdf.add_page()

    # ln() uses argument h.
    pdf.x += 20
    prev_y = pdf.y
    h = 15.0
    pdf.ln(h)
    assert math.isclose(
        pdf.y - prev_y, h
    ), f"ln() didn't move y by argument h ({pdf.y-prev_y} vs. {h})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() with argument h didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."

    # bad argument h
    with pytest.raises(TypeError):
        pdf.ln("hello")


def test_ln_by_lasth():
    pdf = FPDF()
    pdf.add_page()

    # ln() uses self._lasth after writing some text.
    pdf.set_font("helvetica", size=16)
    pdf.x += 20
    pdf.cell(txt="something")
    h = pdf.font_size  # last *used* font height, no cell height given
    prev_y = pdf.y
    pdf.ln(h)
    assert math.isclose(
        pdf.y - prev_y, pdf._lasth
    ), f"ln() after cell() didn't move y by font height ({pdf.y-prev_y} vs. {h})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() after cell() didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."

    # once we have a self._lasth, changing the font size without writing anything should
    # not affect the movement.
    pdf.set_font("helvetica", size=36)
    prev_y = pdf.y
    pdf.ln(h)
    assert math.isclose(
        pdf.y - prev_y, pdf._lasth
    ), f"ln() after cell() didn't move y by font height ({pdf.y-prev_y} vs. {h})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() after cell() didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."

    # cell(h=x) should set _lasth to that
    h = 20
    pdf.x += 33
    pdf.cell(h=h, txt="something")
    prev_y = pdf.y
    pdf.ln()
    assert math.isclose(
        pdf.y - prev_y, h
    ), f"ln() after cell() didn't move y by cell height ({pdf.y-prev_y} vs. {h})."
    assert (
        pdf.x == pdf.l_margin
    ), f"ln() after cell() didn't move x to l_margin ({pdf.x} vs. {pdf.l_margin})."
