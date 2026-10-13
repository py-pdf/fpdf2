from io import BytesIO

import pytest
from defusedxml.ElementTree import fromstring
from pypdf import PdfReader

from fpdf import FPDF
from fpdf.drawing import GradientPaint
from fpdf.enums import GradientUnits
from fpdf.svg import SVGObject


def test_linear_gradient_parsing():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad1)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    # Check gradient was parsed
    assert len(svg_obj.gradient_definitions) == 1
    assert "#grad1" in svg_obj.gradient_definitions
    assert isinstance(svg_obj.gradient_definitions["#grad1"], GradientPaint)


def test_radial_gradient_parsing():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="grad2" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="yellow" />
          <stop offset="100%" stop-color="green" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="80" fill="url(#grad2)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    # Check gradient was parsed
    assert len(svg_obj.gradient_definitions) == 1
    assert "#grad2" in svg_obj.gradient_definitions


def test_multiple_gradients():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad1">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
        <radialGradient id="grad2">
          <stop offset="0%" stop-color="yellow" />
          <stop offset="100%" stop-color="green" />
        </radialGradient>
      </defs>
      <rect width="100" height="200" fill="url(#grad1)" />
      <rect x="100" width="100" height="200" fill="url(#grad2)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert len(svg_obj.gradient_definitions) == 2
    assert "#grad1" in svg_obj.gradient_definitions
    assert "#grad2" in svg_obj.gradient_definitions


def test_gradient_with_multiple_stops():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="rainbow">
          <stop offset="0%" stop-color="red" />
          <stop offset="20%" stop-color="orange" />
          <stop offset="40%" stop-color="yellow" />
          <stop offset="60%" stop-color="green" />
          <stop offset="80%" stop-color="blue" />
          <stop offset="100%" stop-color="purple" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#rainbow)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert len(svg_obj.gradient_definitions) == 1
    assert "#rainbow" in svg_obj.gradient_definitions


def test_gradient_with_opacity():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="fade">
          <stop offset="0%" stop-color="red" stop-opacity="1.0" />
          <stop offset="100%" stop-color="red" stop-opacity="0.0" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#fade)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#fade" in svg_obj.gradient_definitions


@pytest.mark.parametrize("opacity", ["0.5", "50%"])
def test_gradient_stop_opacity_multiplies_color_alpha(opacity):
    gradient = fromstring(
        '<linearGradient xmlns="http://www.w3.org/2000/svg">'
        f'<stop offset="0" stop-color="#ff000080" stop-opacity="{opacity}" />'
        '<stop offset="1" stop-color="blue" />'
        "</linearGradient>"
    )
    # pylint: disable=protected-access
    stops = SVGObject._parse_gradient_stops(gradient)
    # pylint: enable=protected-access
    assert len(stops) == 2
    assert stops[0][1].a == pytest.approx((128 / 255) * 0.5)


@pytest.mark.parametrize("gradient_type", ["linearGradient", "radialGradient"])
def test_gradient_percentage_opacity_preserves_transparent_color(gradient_type):
    svg = f"""
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <{gradient_type} id="fade">
          <stop offset="0" stop-color="#ff000000" stop-opacity="50%" />
          <stop offset="1" stop-color="blue" />
        </{gradient_type}>
      </defs>
      <rect width="200" height="200" fill="url(#fade)" />
    </svg>
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.image(svg.encode(), x=10, y=10, w=20)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    states = dict(page["/Resources"]["/ExtGState"])
    mask = next(
        state.get_object()["/SMask"]
        for state in states.values()
        if "/SMask" in state.get_object()
    )
    patterns = mask["/G"]["/Resources"]["/Pattern"]
    shading = next(iter(patterns.values())).get_object()["/Shading"]
    assert shading["/Function"]["/C0"] == [0]


def test_gradient_units_objectBoundingBox():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" gradientUnits="objectBoundingBox">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions
    assert (
        svg_obj.gradient_definitions["#grad"].units == GradientUnits.OBJECT_BOUNDING_BOX
    )


def test_gradient_units_userSpaceOnUse():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="200" y2="0">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert (
        svg_obj.gradient_definitions["#grad"].units == GradientUnits.USER_SPACE_ON_USE
    )


def test_gradient_spread_methods():
    for spread in ["pad", "reflect", "repeat"]:
        svg = f"""
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad" spreadMethod="{spread}">
              <stop offset="0%" stop-color="red" />
              <stop offset="50%" stop-color="blue" />
            </linearGradient>
          </defs>
          <rect width="200" height="200" fill="url(#grad)" />
        </svg>
        """
        svg_obj = SVGObject(svg)
        assert "#grad" in svg_obj.gradient_definitions


def test_gradient_on_stroke():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="180" height="180" x="10" y="10" 
            fill="none" stroke="url(#grad)" stroke-width="10" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_gradient_with_gradientTransform():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" gradientTransform="rotate(45)">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_radial_gradient_with_focal_point():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="grad" cx="50%" cy="50%" r="50%" fx="25%" fy="25%">
          <stop offset="0%" stop-color="white" />
          <stop offset="100%" stop-color="black" />
        </radialGradient>
      </defs>
      <circle cx="100" cy="100" r="80" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_gradient_stops_with_style_attribute():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad">
          <stop offset="0%" style="stop-color:red;stop-opacity:1" />
          <stop offset="100%" style="stop-color:blue;stop-opacity:0.5" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


@pytest.mark.parametrize("gradient_type", ["linearGradient", "radialGradient"])
@pytest.mark.parametrize(
    ("attribute", "style", "expected_opacity"),
    [
        ("50%", "", 0.5),
        ("25%", "stop-opacity:80%", 0.8),
        ("-0.25", "", 0),
        ("-25%", "", 0),
        ("0.5", "stop-opacity:-0.25", 0),
        ("200%", "", 1),
        ("0.9", "stop-opacity:200%", 1),
        ("0.9", "stop-opacity:0.25", 0.25),
        ("0.25", "stop-opacity:0", 0),
        ("0.25", "stop-opacity:1", 1),
        ("0", "stop-opacity:0.5", 0.5),
        ("0.9", "stop-color:blue", 0.9),
        ("0.9", "stop-opacity:invalid", 0.9),
        ("0.9", "", 0.9),
        (None, "stop-opacity:0.25", 0.25),
        (None, "", 1),
    ],
)
def test_gradient_stop_opacity_style_precedence(
    gradient_type, attribute, style, expected_opacity
):
    opacity_attribute = f'stop-opacity="{attribute}"' if attribute is not None else ""
    svg = f"""
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <{gradient_type} id="fade">
          <stop offset="0" stop-color="red" {opacity_attribute} style="{style}" />
          <stop offset="1" stop-color="blue" />
        </{gradient_type}>
      </defs>
      <rect width="200" height="200" fill="url(#fade)" />
    </svg>
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.image(svg.encode(), x=10, y=10, w=20)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    states = dict(page["/Resources"]["/ExtGState"])
    masks = [
        state.get_object()["/SMask"]
        for state in states.values()
        if "/SMask" in state.get_object()
    ]
    if expected_opacity == 1:
        assert not masks
    else:
        assert len(masks) == 1
        patterns = masks[0]["/G"]["/Resources"]["/Pattern"]
        assert len(patterns) == 1
        shading = next(iter(patterns.values())).get_object()["/Shading"]
        assert shading["/ColorSpace"] == "/DeviceGray"
        assert shading["/Function"]["/C0"] == [expected_opacity]
        assert shading["/Function"]["/C1"] == [1]


def test_gradient_without_id_is_skipped():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient>
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="red" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    # Should not crash, just skip the gradient
    assert len(svg_obj.gradient_definitions) == 0


def test_gradient_without_stops_is_skipped():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="empty" />
      </defs>
      <rect width="200" height="200" fill="url(#empty)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    # Gradient should be skipped due to no stops
    assert "#empty" not in svg_obj.gradient_definitions


def test_gradient_percentage_coordinates():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_gradient_absolute_coordinates():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad" gradientUnits="userSpaceOnUse" 
                        x1="0" y1="0" x2="200" y2="200">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="200" height="200" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_gradient_on_path():
    svg = """
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <path d="M 10 10 L 190 10 L 190 190 L 10 190 Z" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions


def test_gradient_on_shapes():
    svg = """
    <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad">
          <stop offset="0%" stop-color="red" />
          <stop offset="100%" stop-color="blue" />
        </linearGradient>
      </defs>
      <rect width="80" height="80" fill="url(#grad)" />
      <circle cx="150" cy="40" r="40" fill="url(#grad)" />
      <ellipse cx="260" cy="40" rx="40" ry="30" fill="url(#grad)" />
      <polygon points="320,10 350,80 290,80" fill="url(#grad)" />
    </svg>
    """
    svg_obj = SVGObject(svg)

    assert "#grad" in svg_obj.gradient_definitions
