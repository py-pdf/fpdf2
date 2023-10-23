from fpdf.fonts import FontFace


def test_combine_fontface():
    font1 = FontFace(family="helvetica", size_pt=12)
    # providing None override should return the default style
    assert FontFace.combine(override_style=None, default_style=font1) == font1
    # overriding a None style should return the override
    assert FontFace.combine(override_style=font1, default_style=None) == font1
    font2 = FontFace(size_pt=14)
    combined = FontFace.combine(override_style=font2, default_style=font1)
    assert isinstance(combined, FontFace)
    assert combined.family == "helvetica"  # wasn't overridden
    assert combined.emphasis is None  # wasn't specified by either
    assert combined.size_pt == 14  # was overridden
