from pathlib import Path

import pytest

import fpdf
from fpdf.line_break import MultiLineBreak, TextLine
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


CELLDATA = (
    # txt,        align, new_x,    new_y
    ["Left Top L", "L", fpdf.XPos.LEFT, fpdf.YPos.TOP],
    ["Left Top R", "R", fpdf.XPos.LEFT, fpdf.YPos.TOP],
    ["Left Top C", "C", fpdf.XPos.LEFT, fpdf.YPos.TOP],
    ["Left Top J", "J", fpdf.XPos.LEFT, fpdf.YPos.TOP],
    ["Right Last L", "L", fpdf.XPos.RIGHT, fpdf.YPos.LAST],
    ["Right Last R", "R", fpdf.XPos.RIGHT, fpdf.YPos.LAST],
    ["Right Last C", "C", fpdf.XPos.RIGHT, fpdf.YPos.LAST],
    ["Right Last J", "J", fpdf.XPos.RIGHT, fpdf.YPos.LAST],
    ["Start Next L", "L", fpdf.XPos.START, fpdf.YPos.NEXT],
    ["Start Next R", "R", fpdf.XPos.START, fpdf.YPos.NEXT],
    ["Start Next C", "C", fpdf.XPos.START, fpdf.YPos.NEXT],
    ["Start Next J", "J", fpdf.XPos.START, fpdf.YPos.NEXT],
    ["End TMargin L", "L", fpdf.XPos.END, fpdf.YPos.TMARGIN],
    ["End TMargin R", "R", fpdf.XPos.END, fpdf.YPos.TMARGIN],
    ["End TMargin C", "C", fpdf.XPos.END, fpdf.YPos.TMARGIN],
    ["End TMargin J", "J", fpdf.XPos.END, fpdf.YPos.TMARGIN],
    ["WCont Top L", "L", fpdf.XPos.WCONT, fpdf.YPos.TOP],
    ["WCont Top R", "R", fpdf.XPos.WCONT, fpdf.YPos.TOP],
    ["WCont Top C", "C", fpdf.XPos.WCONT, fpdf.YPos.TOP],
    ["WCont Top J", "J", fpdf.XPos.WCONT, fpdf.YPos.TOP],
    ["Center TOP L", "L", fpdf.XPos.CENTER, fpdf.YPos.TOP],
    ["Center TOP R", "R", fpdf.XPos.CENTER, fpdf.YPos.TOP],
    ["Center TOP C", "C", fpdf.XPos.CENTER, fpdf.YPos.TOP],
    ["Center TOP J", "J", fpdf.XPos.CENTER, fpdf.YPos.TOP],
    ["LMargin BMargin L", "L", fpdf.XPos.LMARGIN, fpdf.YPos.BMARGIN],
    ["LMargin BMargin R", "R", fpdf.XPos.LMARGIN, fpdf.YPos.BMARGIN],
    ["LMargin BMargin C", "C", fpdf.XPos.LMARGIN, fpdf.YPos.BMARGIN],
    ["LMargin BMargin J", "J", fpdf.XPos.LMARGIN, fpdf.YPos.BMARGIN],
    ["RMargin Top L", "L", fpdf.XPos.RMARGIN, fpdf.YPos.TOP],
    ["RMargin Top R", "R", fpdf.XPos.RMARGIN, fpdf.YPos.TOP],
    ["RMargin Top C", "C", fpdf.XPos.RMARGIN, fpdf.YPos.TOP],
    ["RMargin Top J", "J", fpdf.XPos.RMARGIN, fpdf.YPos.TOP],
)


def test_render_styled_newpos(tmp_path):
    """
    Verify that _render_styled_text_line() places the new position
    in the right places in all possible combinations of alignment,
    new_x, and new_y.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 4
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        newx = item[2]
        newy = item[3]
        # pylint: disable=protected-access
        frags = doc._preload_font_styles(s, False)
        mlb = MultiLineBreak(
            frags,
            doc.get_normalized_string_width_with_style,
            justify=(align == "J"),
        )
        line = mlb.get_line_of_given_width(twidth * 1000 / doc.font_size)
        # we need to manually rebuild our TextLine in order to force
        # justified alignment on a single line.
        line = TextLine(
            fragments=line.fragments,
            text_width=line.text_width,
            number_of_spaces_between_words=line.number_of_spaces_between_words,
            justify=align == "J",
        )
        doc._render_styled_text_line(
            line,
            twidth,
            border=1,
            align=align,
            new_x=newx,
            new_y=newy,
        )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "render_styled_newpos.pdf", tmp_path)


def test_cell_newpos(tmp_path):
    """
    Verify that cell() places the new position
    in the right places in all possible combinations of alignment,
    new_x, and new_y.

    Note:
        cell() doesn't process align="J", and uses "L" instead.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 4
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        newx = item[2]
        newy = item[3]
        doc.cell(
            twidth,
            txt=s,
            border=1,
            align=align,
            new_x=newx,
            new_y=newy,
        )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "cell_newpos.pdf", tmp_path)


def test_multi_cell_newpos(tmp_path):
    """
    Verify that multi_cell() places the new position
    in the right places in all possible combinations of alignment,
    new_x, and new_y.

    Note:
        multi_cell() doesn't use align="J" on the first line, and
        uses "L" instead. new_x is relative to the last line.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 4
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        newx = item[2]
        newy = item[3]
        doc.multi_cell(
            twidth,
            txt=s + " xxxxxxxxxxxxxxx",  # force auto break
            border=1,
            align=align,
            new_x=newx,
            new_y=newy,
        )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "multi_cell_newpos.pdf", tmp_path)


LN_CELLDATA = (
    # txt,     align, ln
    ["ln=0 L", "L", 0],
    ["ln=0 R", "R", 0],
    ["ln=0 C", "C", 0],
    ["ln=0 J", "J", 0],
    ["ln=1 L", "L", 1],
    ["ln=1 R", "R", 1],
    ["ln=1 C", "C", 1],
    ["ln=1 J", "J", 1],
    ["ln=2 L", "L", 2],
    ["ln=2 R", "R", 2],
    ["ln=2 C", "C", 2],
    ["ln=2 J", "J", 2],
    ["ln=3 L", "L", 3],
    ["ln=3 R", "R", 3],
    ["ln=3 C", "C", 3],
    ["ln=3 J", "J", 3],
)


def test_cell_lnpos(tmp_path):
    """
    Verify that cell() places the new position
    in the right places in all possible combinations of alignment,
    and (deprecated) ln=#.

    Note:
        cell() doesn't process align="J", and uses "L" instead.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    for i, item in enumerate(LN_CELLDATA):
        i = i % 4
        ln = item[2]
        if ln > 2:  # not valid for cell()
            break
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        with pytest.warns(DeprecationWarning):
            doc.cell(
                twidth,
                txt=s,
                border=1,
                align=align,
                ln=ln,
            )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "cell_ln_newpos.pdf", tmp_path)


def test_multi_cell_ln_newpos(tmp_path):
    """
    Verify that multi_cell() places the new position
    in the right places in all possible combinations of alignment,
    and (deprecated) ln=#.

    Note:
        multi_cell() doesn't use align="J" on the first line, and
        uses "L" instead. new_x is relative to the last line.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    for i, item in enumerate(LN_CELLDATA):
        i = i % 4
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        ln = item[2]
        with pytest.warns(DeprecationWarning):
            doc.multi_cell(
                twidth,
                txt=s + " xxxxxxxxxxxxxxxxxxxx",  # force auto break
                border=1,
                align=align,
                ln=ln,
            )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "multi_cell_ln_newpos.pdf", tmp_path)
