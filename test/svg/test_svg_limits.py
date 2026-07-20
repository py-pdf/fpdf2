from pathlib import Path

import pytest

import fpdf
from fpdf.errors import FPDFSvgLimitExceeded
from fpdf.svg import SVGObject, SVGLimits


def _nested_use_svg(level: int, fanout: int = 2) -> bytes:
    groups = ['<g id="g0"><rect width="1" height="1"/></g>']
    for current_level in range(1, level + 1):
        uses = f'<use href="#g{current_level - 1}"/>' * fanout
        groups.append(f'<g id="g{current_level}">{uses}</g>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
        "<defs>" + "".join(groups) + f'</defs><use href="#g{level}"/></svg>'
    ).encode()


def _reverse_nested_use_svg(level: int) -> bytes:
    groups = [
        f'<g id="g{current_level}"><use href="#g{current_level - 1}"/></g>'
        for current_level in range(level, 0, -1)
    ]
    groups.append('<g id="g0"><rect width="1" height="1"/></g>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
        "<defs>" + "".join(groups) + f'</defs><use href="#g{level}"/></svg>'
    ).encode()


def test_default_svg_limits() -> None:
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


def test_svg_limits_reject_use_cycles() -> None:
    svg = b"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">
      <defs>
        <g id="a"><use href="#b"/></g>
        <g id="b"><use href="#a"/></g>
      </defs>
      <use href="#a"/>
    </svg>
    """

    with pytest.raises(fpdf.FPDFException, match="cycle"):
        SVGObject(svg)


def test_svg_limits_reject_excessive_use_depth() -> None:
    with pytest.raises(FPDFSvgLimitExceeded, match="max_use_depth"):
        SVGObject(_nested_use_svg(level=2), svg_limits=SVGLimits(max_use_depth=1))


def test_svg_limits_reject_deep_reverse_ordered_use_chain() -> None:
    with pytest.raises(FPDFSvgLimitExceeded, match="max_use_depth"):
        SVGObject(_reverse_nested_use_svg(level=1100))


def test_image_uses_svg_resolved_element_limit() -> None:
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.svg_limits = SVGLimits(max_resolved_elements=20)

    with pytest.raises(fpdf.FPDFException, match="max_resolved_elements"):
        pdf.image(_nested_use_svg(level=2, fanout=4), w=10)


def test_image_preserves_limit_exception(tmp_path: Path) -> None:
    svg_file = tmp_path / "heavy.svg"
    svg_file.write_bytes(_nested_use_svg(level=2, fanout=4))
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.svg_limits = SVGLimits(max_resolved_elements=20)

    with pytest.raises(fpdf.FPDFException, match="max_resolved_elements"):
        pdf.image(svg_file, w=10)


def test_disable_complexity_limits() -> None:
    svg = SVGObject(
        _nested_use_svg(level=3, fanout=4),
        svg_limits=SVGLimits(max_use_depth=None, max_resolved_elements=None),
    )

    assert svg.base_group is not None
