from pathlib import Path

import pytest

import fpdf
from fpdf.line_break import MultiLineBreak
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_render_styled_newpos(tmp_path):
    doc = fpdf.FPDF()
    # doc.add_page()
    doc.set_font("helvetica", size=24)
    doc.set_margin(10)
    twidth = 100

    data = (
        # txt,        align, newpos_x,    newpos_y,   target x/y
        ["Left Top L", "L", fpdf.X.LEFT, fpdf.Y.TOP, 20, 20],
        ["Left Top R", "R", fpdf.X.LEFT, fpdf.Y.TOP, 20, 20],
        ["Left Top C", "C", fpdf.X.LEFT, fpdf.Y.TOP, 20, 20],
        ["Left Top J", "J", fpdf.X.LEFT, fpdf.Y.TOP, 20, 20],
        ["Right Last L", "L", fpdf.X.RIGHT, fpdf.Y.LAST, 70, 30],
        ["Right Last R", "R", fpdf.X.RIGHT, fpdf.Y.LAST, 70, 30],
        ["Right Last C", "C", fpdf.X.RIGHT, fpdf.Y.LAST, 70, 30],
        ["Right Last J", "J", fpdf.X.RIGHT, fpdf.Y.LAST, 70, 30],
        ["Start Next L", "L", fpdf.X.START, fpdf.Y.NEXT, "s", 40 + doc.font_size],
        ["Start Next R", "R", fpdf.X.START, fpdf.Y.NEXT, "s", 40 + doc.font_size],
        ["Start Next C", "C", fpdf.X.START, fpdf.Y.NEXT, "s", 40 + doc.font_size],
        ["Start Next J", "J", fpdf.X.START, fpdf.Y.NEXT, "s", 40 + doc.font_size],
        ["End TMargin L", "L", fpdf.X.END, fpdf.Y.TMARGIN, "e", 10],
        ["End TMargin R", "R", fpdf.X.END, fpdf.Y.TMARGIN, "e", 10],
        ["End TMargin C", "C", fpdf.X.END, fpdf.Y.TMARGIN, "e", 10],
        ["End TMargin J", "J", fpdf.X.END, fpdf.Y.TMARGIN, "e", 10],
        ["Center TOP L", "L", fpdf.X.CENTER, fpdf.Y.TOP, 50, doc.h - 10],
        ["Center TOP R", "R", fpdf.X.CENTER, fpdf.Y.TOP, 50, doc.h - 10],
        ["Center TOP C", "C", fpdf.X.CENTER, fpdf.Y.TOP, 50, doc.h - 10],
        ["Center TOP J", "J", fpdf.X.CENTER, fpdf.Y.TOP, 50, doc.h - 10],
        ["LMargin BMargin L", "L", fpdf.X.LMARGIN, fpdf.Y.BMARGIN, 10, 70],
        ["LMargin BMargin R", "R", fpdf.X.LMARGIN, fpdf.Y.BMARGIN, 10, 70],
        ["LMargin BMargin C", "C", fpdf.X.LMARGIN, fpdf.Y.BMARGIN, 10, 70],
        ["LMargin BMargin J", "J", fpdf.X.LMARGIN, fpdf.Y.BMARGIN, 10, 70],
        ["RMargin Top L", "L", fpdf.X.RMARGIN, fpdf.Y.TOP, doc.w - 10, 80],
        ["RMargin Top R", "R", fpdf.X.RMARGIN, fpdf.Y.TOP, doc.w - 10, 80],
        ["RMargin Top C", "C", fpdf.X.RMARGIN, fpdf.Y.TOP, doc.w - 10, 80],
        ["RMargin Top J", "J", fpdf.X.RMARGIN, fpdf.Y.TOP, doc.w - 10, 80],
    )

    for i, item in enumerate(data):
        i = i % 4
        if i == 0:
            doc.add_page()
        doc.x = 20
        doc.y = 20 + (i * 20)
        s = item[0]
        align = item[1]
        newx = item[2]
        newy = item[3]
        expx = item[4]
        expy = item[5]
        frags = doc._preload_font_styles(s, False)
        mlb = MultiLineBreak(
            frags,
            doc.get_normalized_string_width_with_style,
            justify=(align == "J"),
        )
        line = mlb.get_line_of_given_width(twidth * 1000 / doc.font_size)
        new_page = doc._render_styled_cell_text(
            twidth,
            styled_txt_frags=line.fragments,
            border=1,
            align=align,  # "L" if align == "J" else align,
            newpos_x=newx,
            newpos_y=newy,
        )
        sw = doc.get_string_width(line.fragments[0].string)
        if expx == "s":
            expx = doc.x + twidth - sw
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)
        # assert doc.x == expx, f"Resulting x position {doc.x} != {expx}"
        # assert doc.y == expy, f"Resulting y position {doc.y} != {expy}"

    assert_pdf_equal(doc, HERE / "render_styled_newpos.pdf", tmp_path)
