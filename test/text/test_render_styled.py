from pathlib import Path

import pytest

import fpdf
from fpdf.enums import Align, XPos, YPos
from fpdf.line_break import MultiLineBreak, TextLine
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


CELLDATA = (
    # txt,        align, new_x,    new_y
    ("Left Top L", "L", "LEFT", "TOP"),
    ("Left Top R", "R", "LEFT", "TOP"),
    ("Left Top C", "C", "LEFT", "TOP"),
    ("Left Top X", "X", "LEFT", "TOP"),
    ("Left Top J", "J", "LEFT", "TOP"),
    ("Right Last L", "L", "RIGHT", "LAST"),
    ("Right Last R", "R", "RIGHT", "LAST"),
    ("Right Last C", "C", "RIGHT", "LAST"),
    ("Right Last X", "X", "RIGHT", "LAST"),
    ("Right Last J", "J", "RIGHT", "LAST"),
    ("Start Next L", "L", "START", "NEXT"),
    ("Start Next R", "R", "START", "NEXT"),
    ("Start Next C", "C", "START", "NEXT"),
    ("Start Next X", "X", "START", "NEXT"),
    ("Start Next J", "J", "START", "NEXT"),
    ("End TMargin L", "L", "END", "TMARGIN"),
    ("End TMargin R", "R", "END", "TMARGIN"),
    ("End TMargin C", "C", "END", "TMARGIN"),
    ("End TMargin X", "X", "END", "TMARGIN"),
    ("End TMargin J", "J", "END", "TMARGIN"),
    ("WCont Top L", "L", "WCONT", "TOP"),
    ("WCont Top R", "R", "WCONT", "TOP"),
    ("WCont Top C", "C", "WCONT", "TOP"),
    ("WCont Top X", "X", "WCONT", "TOP"),
    ("WCont Top J", "J", "WCONT", "TOP"),
    ("Center TOP L", "L", "CENTER", "TOP"),
    ("Center TOP R", "R", "CENTER", "TOP"),
    ("Center TOP C", "C", "CENTER", "TOP"),
    ("Center TOP X", "X", "CENTER", "TOP"),
    ("Center TOP J", "J", "CENTER", "TOP"),
    ("LMargin BMargin L", "L", "LMARGIN", "BMARGIN"),
    ("LMargin BMargin R", "R", "LMARGIN", "BMARGIN"),
    ("LMargin BMargin C", "C", "LMARGIN", "BMARGIN"),
    ("LMargin BMargin X", "X", "LMARGIN", "BMARGIN"),
    ("LMargin BMargin J", "J", "LMARGIN", "BMARGIN"),
    ("RMargin Top L", "L", "RMARGIN", "TOP"),
    ("RMargin Top R", "R", "RMARGIN", "TOP"),
    ("RMargin Top C", "C", "RMARGIN", "TOP"),
    ("RMargin Top X", "X", "RMARGIN", "TOP"),
    ("RMargin Top J", "J", "RMARGIN", "TOP"),
)


def test_render_styled_newpos(tmp_path):
    """
    Verify that _render_styled_text_line() places the new position
    in the right places in all possible combinations of alignment,
    new_x, and new_y.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 5
        if i == 0:
            doc.add_page()
        doc.x = 70
        doc.y = 20 + (i * 20)
        s = item[0]
        align = Align.coerce(item[1])
        newx = XPos.coerce(item[2])
        newy = YPos.coerce(item[3])
        # pylint: disable=protected-access
        frags = doc._preload_font_styles(s, False)
        mlb = MultiLineBreak(
            frags,
            doc.get_normalized_string_width_with_style,
            justify=(align == Align.J),
        )
        line = mlb.get_line_of_given_width(twidth * 1000 / doc.font_size)
        # we need to manually rebuild our TextLine in order to force
        # justified alignment on a single line.
        line = TextLine(
            fragments=line.fragments,
            text_width=line.text_width,
            number_of_spaces_between_words=line.number_of_spaces_between_words,
            justify=align == Align.J,
            trailing_nl=False,
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
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 5
        if i == 0:
            doc.add_page()
        doc.x = 70
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        if align == "J":
            continue
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
    twidth = 100

    for i, item in enumerate(CELLDATA):
        i = i % 5
        if i == 0:
            doc.add_page()
        doc.x = 70
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
    # txt, align, ln
    ("ln=0 L", "L", 0),
    ("ln=0 R", "R", 0),
    ("ln=0 C", "C", 0),
    ("ln=0 J", "J", 0),
    ("ln=1 L", "L", 1),
    ("ln=1 R", "R", 1),
    ("ln=1 C", "C", 1),
    ("ln=1 J", "J", 1),
    ("ln=2 L", "L", 2),
    ("ln=2 R", "R", 2),
    ("ln=2 C", "C", 2),
    ("ln=2 J", "J", 2),
    ("ln=3 L", "L", 3),
    ("ln=3 R", "R", 3),
    ("ln=3 C", "C", 3),
    ("ln=3 J", "J", 3),
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
        if align == "J":
            continue
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
