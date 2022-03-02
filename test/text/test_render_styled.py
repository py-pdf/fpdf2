from pathlib import Path

import fpdf
from fpdf.line_break import MultiLineBreak
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_render_styled_newpos(tmp_path):
    """
    Verify that _render_styled_cell_text() places the new position
    in the right places in all possible combinations of alignment,
    newpos_x, and newpos_y.
    """
    doc = fpdf.FPDF()
    doc.set_font("helvetica", style="U", size=24)
    doc.set_margin(10)
    twidth = 100

    data = (
        # txt,        align, newpos_x,    newpos_y
        ["Left Top L", "L", fpdf.X.LEFT, fpdf.Y.TOP],
        ["Left Top R", "R", fpdf.X.LEFT, fpdf.Y.TOP],
        ["Left Top C", "C", fpdf.X.LEFT, fpdf.Y.TOP],
        ["Left Top J", "J", fpdf.X.LEFT, fpdf.Y.TOP],
        ["Right Last L", "L", fpdf.X.RIGHT, fpdf.Y.LAST],
        ["Right Last R", "R", fpdf.X.RIGHT, fpdf.Y.LAST],
        ["Right Last C", "C", fpdf.X.RIGHT, fpdf.Y.LAST],
        ["Right Last J", "J", fpdf.X.RIGHT, fpdf.Y.LAST],
        ["Start Next L", "L", fpdf.X.START, fpdf.Y.NEXT],
        ["Start Next R", "R", fpdf.X.START, fpdf.Y.NEXT],
        ["Start Next C", "C", fpdf.X.START, fpdf.Y.NEXT],
        ["Start Next J", "J", fpdf.X.START, fpdf.Y.NEXT],
        ["End TMargin L", "L", fpdf.X.END, fpdf.Y.TMARGIN],
        ["End TMargin R", "R", fpdf.X.END, fpdf.Y.TMARGIN],
        ["End TMargin C", "C", fpdf.X.END, fpdf.Y.TMARGIN],
        ["End TMargin J", "J", fpdf.X.END, fpdf.Y.TMARGIN],
        ["WCont Top L", "L", fpdf.X.WCONT, fpdf.Y.TOP],
        ["WCont Top R", "R", fpdf.X.WCONT, fpdf.Y.TOP],
        ["WCont Top C", "C", fpdf.X.WCONT, fpdf.Y.TOP],
        ["WCont Top J", "J", fpdf.X.WCONT, fpdf.Y.TOP],
        ["Center TOP L", "L", fpdf.X.CENTER, fpdf.Y.TOP],
        ["Center TOP R", "R", fpdf.X.CENTER, fpdf.Y.TOP],
        ["Center TOP C", "C", fpdf.X.CENTER, fpdf.Y.TOP],
        ["Center TOP J", "J", fpdf.X.CENTER, fpdf.Y.TOP],
        ["LMargin BMargin L", "L", fpdf.X.LMARGIN, fpdf.Y.BMARGIN],
        ["LMargin BMargin R", "R", fpdf.X.LMARGIN, fpdf.Y.BMARGIN],
        ["LMargin BMargin C", "C", fpdf.X.LMARGIN, fpdf.Y.BMARGIN],
        ["LMargin BMargin J", "J", fpdf.X.LMARGIN, fpdf.Y.BMARGIN],
        ["RMargin Top L", "L", fpdf.X.RMARGIN, fpdf.Y.TOP],
        ["RMargin Top R", "R", fpdf.X.RMARGIN, fpdf.Y.TOP],
        ["RMargin Top C", "C", fpdf.X.RMARGIN, fpdf.Y.TOP],
        ["RMargin Top J", "J", fpdf.X.RMARGIN, fpdf.Y.TOP],
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
        # pylint: disable=protected-access
        frags = doc._preload_font_styles(s, False)
        mlb = MultiLineBreak(
            frags,
            doc.get_normalized_string_width_with_style,
            justify=(align == "J"),
        )
        line = mlb.get_line_of_given_width(twidth * 1000 / doc.font_size)
        doc._render_styled_cell_text(
            line,
            twidth,
            border=1,
            align=align,  # "L" if align == "J" else align,
            newpos_x=newx,
            newpos_y=newy,
        )
        # mark the new position in the file with crosshairs for verification
        with doc.rotation(i * -15, doc.x, doc.y):
            doc.circle(doc.x - 3, doc.y - 3, 6)
            doc.line(doc.x - 3, doc.y, doc.x + 3, doc.y)
            doc.line(doc.x, doc.y - 3, doc.x, doc.y + 3)

    assert_pdf_equal(doc, HERE / "render_styled_newpos.pdf", tmp_path)
