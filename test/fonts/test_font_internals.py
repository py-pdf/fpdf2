import pytest

from fpdf.fonts import Glyph
from fpdf.output import (  # pylint: disable=import-private-name
    _cid_font_widths,
    _tt_font_widths,
)


def test_glyph_class():
    glyph = Glyph(glyph_id=32, unicode=(0,), glyph_name=".notdef", glyph_width=0)
    # pylint: disable=comparison-with-itself
    assert glyph == glyph
    assert hash(glyph) == hash(glyph)


@pytest.mark.parametrize(
    "cid_widths,expected_output",
    [
        ({1: 500, 2: 500, 3: 500}, "[ 1 3 500]"),
        ({1: 250, 2: 300, 3: 350}, "[ 1 [ 250 300 350 ]\n]"),
        ({1: 500, 4: 600, 5: 600}, "[ 1 1 500 4 5 600]"),
    ],
)
def test_cid_and_tt_font_widths(cid_widths, expected_output):
    assert _cid_font_widths(cid_widths) == expected_output

    class DummyTTFFont:
        def __init__(self, widths):
            self.subset = {
                Glyph(
                    glyph_id=cid,
                    unicode=(cid,),
                    glyph_name=f"g{cid}",
                    glyph_width=w,
                ): cid
                for cid, w in widths.items()
            }

    dummy_font = DummyTTFFont(cid_widths)
    assert _tt_font_widths(dummy_font) == expected_output
