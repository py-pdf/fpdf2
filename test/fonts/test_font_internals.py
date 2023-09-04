from fpdf.fonts import Glyph


def test_glyph_class():
    glyph = Glyph(glyph_id=32, unicode=(0,), glyph_name=".notdef", glyph_width=0)
    # pylint: disable=comparison-with-itself
    assert glyph == glyph
    assert hash(glyph) == hash(glyph)
