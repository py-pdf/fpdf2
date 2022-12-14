import fpdf
import pytest


def test_rect_transform_width_exception():
    svg_data = """<?xml version="1.0" standalone="no"?>
    <svg width="10%" height="10cm" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" version="1.1">
    </svg>
    """

    svg = fpdf.svg.SVGObject(svg_data)
    with pytest.raises(ValueError) as error:
        svg.transform_to_rect_viewport(scale=1, width=None, height=10)
    assert 'SVG "width" is a percentage, hence a viewport width is required' == str(
        error.value
    )


def test_rect_transform_height_exception():
    svg_data = """<?xml version="1.0" standalone="no"?>
    <svg width="10cm" height="10%" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" version="1.1">
    </svg>
    """

    svg = fpdf.svg.SVGObject(svg_data)
    with pytest.raises(ValueError) as error:
        svg.transform_to_rect_viewport(1, 10, None)
    assert 'SVG "height" is a percentage, hence a viewport height is required' == str(
        error.value
    )


def test_rect_transform_vw_zero():
    svg_data = """<?xml version="1.0" standalone="no"?>
    <svg width="10cm" height="10cm" viewBox="0 0 0 1000" xmlns="http://www.w3.org/2000/svg" version="1.1">
    </svg>
    """

    svg = fpdf.svg.SVGObject(svg_data)
    width, height, context = svg.transform_to_rect_viewport(2, 10, 5)
    assert width == 0
    assert height == 0
    assert context is not None
