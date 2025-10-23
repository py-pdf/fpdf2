import pytest

from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).resolve().parent


def test_TitleStyle_deprecation():
    # pylint: disable=import-outside-toplevel
    with pytest.warns(DeprecationWarning):
        from fpdf import TitleStyle

        TitleStyle()

    with pytest.warns(DeprecationWarning):
        from fpdf.fonts import TitleStyle

        TitleStyle()


def test_add_font_uni_deprecation():
    pdf = FPDF()

    with pytest.warns(DeprecationWarning) as record:
        # pylint: disable=unexpected-keyword-arg
        pdf.add_font(
            "DejaVu",
            "",
            HERE.parent / "fonts" / "DejaVuSans.ttf",
            uni=True,
        )
    assert len(record) == 1
    assert (
        str(record[0].message)
        == 'Parameter(s) "uni" is deprecated and will be removed in a future release.'
    )


def test_output_dest_deprecation(tmp_path):
    pdf = FPDF()

    with pytest.warns(DeprecationWarning) as record:
        # pylint: disable=unexpected-keyword-arg
        pdf.output(name=tmp_path / "test.pdf", dest="S")
    assert len(record) == 1
    assert (
        str(record[0].message)
        == 'Parameter(s) "dest" is deprecated and will be removed in a future release.'
    )
