from filecmp import cmp

import fpdf
import pytest

from test.conftest import assert_same_file


def test_repeated_calls_to_output(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output(tmp_path / "empty.pdf")
    pdf.output(tmp_path / "empty2.pdf")
    assert cmp(tmp_path / "empty.pdf", tmp_path / "empty2.pdf")


def test_deprecation_warning(tmp_path):
    pdf = fpdf.FPDF()
    with pytest.warns(DeprecationWarning) as record:
        # pylint: disable=unexpected-keyword-arg
        pdf.output(name=tmp_path / "empty.pdf", dest="F")
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)


def test_save_to_absolute_path(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output((tmp_path / "empty.pdf").absolute())


def test_page_dimensions_trailing_zeros_preserve_rounding():
    pdf = fpdf.FPDF(unit="pt", format=(100.0, 200.1234))
    pdf.add_page()
    assert b"/MediaBox [0 0 100 200.12]" in pdf.output()


def test_resolve_font_family_does_not_add_fonts():
    catalog = fpdf.output.ResourceCatalog()
    assert catalog.resolve_font_family("Verdana, sans-serif", "B") == "helvetica"
    assert catalog.resolve_font_family("'Times New Roman'") == "times"
    assert not catalog.font_registry
    with pytest.raises(KeyError):
        catalog.resolve_font_family("")
    with pytest.raises(KeyError):
        catalog.resolve_font_family("no_such_font")


def test_get_font_from_family_symbol_ignores_style():
    catalog = fpdf.output.ResourceCatalog()
    symbol = catalog.get_font_from_family("Symbol", "B")
    assert symbol.fontkey == "symbol"
    assert catalog.get_font_from_family("symbol", "I") is symbol
