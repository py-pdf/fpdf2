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
    assert (
        str(error.value)
        == 'SVG "width" is a percentage, hence a viewport width is required'
    )


def test_rect_transform_height_exception():
    svg_data = """<?xml version="1.0" standalone="no"?>
    <svg width="10cm" height="10%" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" version="1.1">
    </svg>
    """

    svg = fpdf.svg.SVGObject(svg_data)
    with pytest.raises(ValueError) as error:
        svg.transform_to_rect_viewport(scale=1, width=10, height=None)
    assert (
        str(error.value)
        == 'SVG "height" is a percentage, hence a viewport height is required'
    )


def test_rect_transform_vw_zero():
    svg_data = """<?xml version="1.0" standalone="no"?>
    <svg width="10cm" height="10cm" viewBox="0 0 0 1000" xmlns="http://www.w3.org/2000/svg" version="1.1">
    </svg>
    """

    svg = fpdf.svg.SVGObject(svg_data)
    width, height, context = svg.transform_to_rect_viewport(scale=2, width=10, height=5)
    assert width == 0
    assert height == 0
    assert context is not None


@pytest.mark.parametrize(
    "attribute", ['width="0"', 'height="0"', 'width="0%"', 'height="0%"']
)
def test_rect_transform_zero_svg_size_disables_rendering(attribute):
    svg = fpdf.svg.SVGObject(
        f'<svg xmlns="http://www.w3.org/2000/svg" {attribute} viewBox="0 0 10 10">'
        '<rect width="10" height="10"/></svg>'
    )
    width, height, context = svg.transform_to_rect_viewport(
        scale=1, width=20, height=30
    )
    assert (width, height) == (0, 0)
    assert context.path_items == []


@pytest.mark.parametrize("dimensions", [(0, 30), (20, 0)])
def test_rect_transform_zero_viewport_disables_rendering(dimensions):
    svg = fpdf.svg.SVGObject(
        '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
    )
    width, height, context = svg.transform_to_rect_viewport(
        scale=1, width=dimensions[0], height=dimensions[1]
    )
    assert (width, height) == (0, 0)
    assert context.path_items == []


def test_rect_transform_unspecified_size_uses_viewport():
    svg = fpdf.svg.SVGObject(
        '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
    )
    width, height, context = svg.transform_to_rect_viewport(
        scale=1, width=20, height=30
    )
    assert (width, height) == (20, 30)
    assert context.path_items


def test_rect_transform_ignoring_zero_top_attrs_uses_viewport():
    svg = fpdf.svg.SVGObject(
        '<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"><rect width="10" height="10"/></svg>'
    )
    width, height, context = svg.transform_to_rect_viewport(
        scale=1, width=20, height=30, ignore_svg_top_attrs=True
    )
    assert (width, height) == (20, 30)
    assert context.path_items


@pytest.mark.parametrize(
    "attributes",
    [
        'width="0" height="10"',
        'width="10" height="0"',
        'viewBox="0 0 0 10"',
        'viewBox="0 0 10 0"',
    ],
)
def test_draw_zero_sized_svg_at_position(attributes):
    pdf = fpdf.FPDF()
    pdf.add_page()
    previous_position = (pdf.x, pdf.y)
    svg = fpdf.svg.SVGObject(
        f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}>'
        '<rect width="10" height="10"/></svg>'
    )
    svg.draw_to_page(pdf, x=10, y=10)
    assert (pdf.x, pdf.y) == previous_position
    assert b" re" not in pdf.pages[1].contents
