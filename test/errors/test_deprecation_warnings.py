import pytest


def test_TitleStyle_deprecation():
    # pylint: disable=import-outside-toplevel
    with pytest.warns(DeprecationWarning):
        from fpdf import TitleStyle

        TitleStyle()

    with pytest.warns(DeprecationWarning):
        from fpdf.fpdf import TitleStyle

        TitleStyle()
