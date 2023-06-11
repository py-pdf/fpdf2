from filecmp import cmp

import fpdf
import pytest


def test_repeated_calls_to_output(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output(tmp_path / "empty.pdf")
    pdf.output(tmp_path / "empty2.pdf")
    assert cmp(tmp_path / "empty.pdf", tmp_path / "empty2.pdf")


def test_deprecation_warning(tmp_path):
    pdf = fpdf.FPDF()
    with pytest.warns(DeprecationWarning):
        pdf.output(tmp_path / "empty.pdf", "F")


def test_save_to_absolute_path(tmp_path):
    pdf = fpdf.FPDF()
    pdf.output((tmp_path / "empty.pdf").absolute())
