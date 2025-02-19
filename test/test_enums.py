import pytest

from fpdf.enums import TextEmphasis


def test_text_emphasis_coerce():
    assert TextEmphasis.coerce("B") == TextEmphasis.B
    assert TextEmphasis.coerce("BOLD") == TextEmphasis.B
    assert TextEmphasis.coerce("I") == TextEmphasis.I
    assert TextEmphasis.coerce("italics") == TextEmphasis.I
    assert TextEmphasis.coerce("U") == TextEmphasis.U
    assert TextEmphasis.coerce("Underline") == TextEmphasis.U
    with pytest.raises(ValueError):
        assert TextEmphasis.coerce("BXXX")
    assert (
        TextEmphasis.coerce("BIU") == TextEmphasis.B | TextEmphasis.I | TextEmphasis.U
    )


def test_text_emphasis_style():
    assert TextEmphasis.coerce("B").style == "B"
    assert TextEmphasis.coerce("IB").style == "BI"
    assert TextEmphasis.coerce("BIU").style == "BIU"


def test_text_emphasis_add():
    assert TextEmphasis.B.add(TextEmphasis.I).add(
        TextEmphasis.U
    ) == TextEmphasis.coerce("BIU")


def test_text_emphasis_remove():
    assert (
        TextEmphasis.coerce("BIU").remove(TextEmphasis.B).remove(TextEmphasis.I)
        == TextEmphasis.U
    )
