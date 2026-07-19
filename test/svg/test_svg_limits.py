import pytest

import fpdf
from fpdf.svg import SVGLimits


def test_fpdf_has_default_svg_limits() -> None:
    pdf = fpdf.FPDF()

    assert isinstance(pdf.svg_limits, SVGLimits)
    assert pdf.svg_limits == SVGLimits()


def test_fpdf_svg_limits_can_be_replaced() -> None:
    pdf = fpdf.FPDF()
    custom_limits = SVGLimits(
        max_use_depth=64,
        max_resolved_elements=500_000,
    )

    pdf.svg_limits = custom_limits

    assert pdf.svg_limits is custom_limits


@pytest.mark.parametrize("max_use_depth", [0, -1])
def test_svg_limits_reject_non_positive_use_depth(max_use_depth: int) -> None:
    with pytest.raises(ValueError, match="must be a positive integer or None"):
        SVGLimits(max_use_depth=max_use_depth)


@pytest.mark.parametrize("max_resolved_elements", [0, -1])
def test_svg_limits_reject_non_positive_resolved_elements(
    max_resolved_elements: int,
) -> None:
    with pytest.raises(ValueError, match="must be a positive integer or None"):
        SVGLimits(max_resolved_elements=max_resolved_elements)


def test_svg_limits_accept_disabled_limits() -> None:
    limits = SVGLimits(max_use_depth=None, max_resolved_elements=None)

    assert limits.max_use_depth is None
    assert limits.max_resolved_elements is None
