"""SVG patterns: definition resolution, placement and PDF references."""

# pylint: disable=no-member
# Pypdf page/resource dictionaries are dynamic.
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from fpdf import FPDF
from fpdf.svg import SVGObject, SVGLimits
from fpdf.errors import FPDFSvgLimitExceeded
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def render_svg(svg):
    pdf = FPDF(unit="pt", format=(120, 120))
    pdf.add_page()
    pdf.image(svg.encode(), x=0, y=0, w=120, h=120)
    return pdf


def patterns_in(pdf):
    reader = PdfReader(BytesIO(pdf.output()))
    return [p.get_object() for p in reader.pages[0]["/Resources"]["/Pattern"].values()]


@pytest.mark.parametrize(
    "units,content_units",
    [
        ("userSpaceOnUse", "userSpaceOnUse"),
        ("userSpaceOnUse", "objectBoundingBox"),
        ("objectBoundingBox", "userSpaceOnUse"),
        ("objectBoundingBox", "objectBoundingBox"),
    ],
)
def test_pattern_units_and_content_units(units, content_units):
    width = "25%" if units == "objectBoundingBox" else "20"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="{units}" patternContentUnits="{content_units}"
      width="{width}" height="{width}"><rect width=".1" height=".1"/></pattern></defs>
      <rect x="10" y="20" width="80" height="80" fill="url(#p)"/>
    </svg>"""
    pattern = patterns_in(render_svg(svg))[0]
    if units == "objectBoundingBox":
        assert pattern["/BBox"] == [0, 0, 0.25, 0.25]
        assert pattern["/Matrix"] == [80, 0, 0, -80, 10, 100]
    else:
        assert pattern["/BBox"] == [0, 0, 20, 20]
        assert pattern["/Matrix"] == [1, 0, 0, -1, 0, 120]
    assert pattern["/PaintType"] == 1


def test_pattern_forward_reference_inheritance():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs>
        <pattern id="p" href="#base" width="30"/>
        <pattern id="base" patternUnits="userSpaceOnUse" width="20" height="20" x="3" y="4">
          <circle cx="10" cy="10" r="4" fill="red"/>
        </pattern>
      </defs>
      <rect width="100" height="100" fill="url(#p)"/>
    </svg>"""
    pattern = patterns_in(render_svg(svg))[0]
    assert pattern["/BBox"] == [0, 0, 30, 20]
    assert pattern["/Matrix"] == [1, 0, 0, -1, 3, 116]
    assert b"1 0 0 rg" in pattern.get_data()


@pytest.mark.parametrize(
    "references",
    [
        '<pattern id="p" href="#q"/><pattern id="q" href="#p"/>',
        '<pattern id="p" width="10" height="10"><rect width="10" height="10" fill="url(#p)"/></pattern>',
    ],
)
def test_pattern_cycles(references):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"><defs>{references}</defs><rect width="100" height="100" fill="url(#p)"/></svg>'
    with pytest.raises(ValueError, match="Cyclic SVG pattern"):
        SVGObject(svg)


def test_pattern_reference_depth_limit():
    svg = """<svg xmlns="http://www.w3.org/2000/svg"><defs>
      <pattern id="p" href="#q"/><pattern id="q" href="#r"/>
      <pattern id="r" width="10" height="10"/></defs>
      <rect width="100" height="100" fill="url(#p)"/></svg>"""
    with pytest.raises(FPDFSvgLimitExceeded, match="max_use_depth"):
        SVGObject(svg, svg_limits=SVGLimits(max_use_depth=2))


def test_nested_transforms_and_reused_svg(tmp_path):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="userSpaceOnUse" width="10" height="10">
        <rect width="4" height="3" fill="red"/>
      </pattern></defs>
      <g transform="translate(20 20)"><g transform="scale(2)">
        <rect width="30" height="30" fill="url(#p)"/>
      </g></g>
    </svg>"""
    pdf = FPDF(unit="pt", format=(120, 120))
    pdf.add_page()
    pdf.image(svg.encode(), x=0, y=0, w=120, h=120)
    pdf.add_page()
    pdf.image(svg.encode(), x=10, y=10, w=120, h=120)
    assert_pdf_equal(
        pdf, HERE / "generated_pdf" / "tiling_nested_transforms.pdf", tmp_path
    )
    reader = PdfReader(BytesIO(pdf.output()))
    for page, expected in zip(
        reader.pages, ((2, 0, 0, -2, 20, 100), (2, 0, 0, -2, 30, 90))
    ):
        pattern = next(iter(page["/Resources"]["/Pattern"].values())).get_object()
        assert pattern["/Matrix"] == list(expected)


@pytest.mark.parametrize("size", ["0", "-1"])
def test_empty_pattern_does_not_paint(size, tmp_path):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="userSpaceOnUse" width="{size}" height="10">
        <rect width="10" height="10" fill="red"/>
      </pattern></defs><rect width="120" height="120" fill="url(#p)"/></svg>"""
    pdf = render_svg(svg)
    assert_pdf_equal(pdf, HERE / "generated_pdf" / "tiling_empty_pattern.pdf", tmp_path)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    assert "/Pattern" not in page["/Resources"]
    assert any(
        state.get_object().get("/ca") == 0
        for state in page["/Resources"]["/ExtGState"].values()
    )


def test_svg_patterns_golden(tmp_path):
    pdf = FPDF(unit="pt", format=(480, 610))
    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.text(20, 28, "SVG tiling patterns")
    pdf.image(HERE / "svg_sources" / "tiling_patterns.svg", x=20, y=40, w=440, h=550)
    pdf.set_font("helvetica", size=10)
    labels = (
        ("User-space tiles and contents", 40, 75),
        ("Bounding-box tiles and contents", 260, 75),
        ("Bounding-box tiles, user-space contents", 40, 255),
        ("User-space tiles, bounding-box contents", 260, 255),
        ("Inherited viewBox and rotation", 40, 435),
        ("Text tile inside a translated group", 260, 435),
    )
    for text, x, y in labels:
        pdf.text(x, y, text)
    assert_pdf_equal(pdf, HERE / "generated_pdf" / "tiling_patterns.pdf", tmp_path)


def assert_svg_golden(pdf, name, tmp_path):
    """Keep visual reference coverage portable without a rasterizer dependency."""
    assert_pdf_equal(pdf, HERE / "generated_pdf" / name, tmp_path)


@pytest.mark.parametrize(
    "units,content_units",
    [
        ("userSpaceOnUse", "userSpaceOnUse"),
        ("userSpaceOnUse", "objectBoundingBox"),
        ("objectBoundingBox", "userSpaceOnUse"),
        ("objectBoundingBox", "objectBoundingBox"),
    ],
)
def test_rendered_independent_coordinate_systems(tmp_path, units, content_units):
    w, h = (".25", ".5") if units == "objectBoundingBox" else ("20", "20")
    cw, ch = (".05", ".1") if content_units == "objectBoundingBox" else ("4", "4")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="{units}" patternContentUnits="{content_units}"
      width="{w}" height="{h}"><rect width="{cw}" height="{ch}" fill="red"/></pattern></defs>
      <rect x="10" y="20" width="80" height="40" fill="url(#p)"/>
    </svg>"""
    assert_svg_golden(
        render_svg(svg), f"tiling_units_{units}_{content_units}.pdf", tmp_path
    )


@pytest.mark.parametrize(
    "preserve",
    ["xMidYMid meet", "xMinYMin meet", "xMaxYMax meet", "none", "xMidYMid slice"],
)
def test_viewbox_aspect_ratio(tmp_path, preserve):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="userSpaceOnUse" patternContentUnits="objectBoundingBox"
      width="20" height="10" viewBox="0 0 10 10" preserveAspectRatio="{preserve}">
        <rect width="10" height="10" fill="red"/>
      </pattern></defs><rect width="120" height="120" fill="url(#p)"/></svg>"""
    assert_svg_golden(
        render_svg(svg), f"tiling_viewbox_{preserve.replace(' ', '_')}.pdf", tmp_path
    )


def test_definition_ancestor_styles_and_nested_patterns(tmp_path):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs fill="red"><pattern id="inner" patternUnits="userSpaceOnUse" width="4" height="4">
        <circle cx="2" cy="2" r="1"/>
      </pattern><pattern id="outer" patternUnits="userSpaceOnUse" width="8" height="8">
        <rect width="8" height="8" fill="url(#inner)"/>
      </pattern></defs><rect width="120" height="120" fill="url(#outer)"/></svg>"""
    assert_svg_golden(render_svg(svg), "tiling_inherited_nested_patterns.pdf", tmp_path)


def test_svg_pattern_stroke_and_text():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="userSpaceOnUse" width="6" height="6">
        <rect width="3" height="6" fill="red"/>
      </pattern></defs>
      <rect x="10" y="10" width="100" height="40" fill="none" stroke="url(#p)" stroke-width="4"/>
      <text x="10" y="100" font-family="Helvetica" font-size="40" fill="url(#p)">fpdf2</text>
    </svg>"""
    pdf = render_svg(svg)
    reader = PdfReader(BytesIO(pdf.output()))
    content = reader.pages[0].get_contents().get_data()
    assert b"/Pattern CS" in content
    assert b"/Pattern cs" in content
    assert b"(fpdf2) Tj" in content


def test_user_space_percentage_tiles(tmp_path):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs><pattern id="p" patternUnits="userSpaceOnUse" width="25%" height="25%">
        <rect width="4" height="4" fill="red"/>
      </pattern></defs><rect width="120" height="120" fill="url(#p)"/></svg>"""
    assert_svg_golden(render_svg(svg), "tiling_user_space_percentages.pdf", tmp_path)


def test_mdn_gradients_inside_bounding_box_tile(tmp_path):
    """The MDN tile scales user-space contents, including both gradients."""
    pdf = FPDF(unit="pt", format=(200, 200))
    pdf.set_margin(0)
    pdf.add_page()
    svg = SVGObject.from_file(HERE / "svg_sources" / "tilling_and_gradient.svg")
    svg.draw_to_page(pdf)
    assert_svg_golden(pdf, "tilling_and_gradient.pdf", tmp_path)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    tile = next(iter(page["/Resources"]["/Pattern"].values())).get_object()
    matrices = sorted(
        tuple(pattern.get_object()["/Matrix"])
        for pattern in tile["/Resources"]["/Pattern"].values()
    )
    # Gradient bounds (25x25 and 40x40 at 5,5) map through the cell's 1/200 scale.
    assert matrices == [(0.125, 0, 0, 0.125, 0, 0), (0.2, 0, 0, 0.2, 0.025, 0.025)]


def test_inherited_pattern_uses_each_shape_bounds(tmp_path):
    """Group inheritance sizes tiles per leaf and respects explicit overrides."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 200">
      <defs><pattern id="p" width=".25" height=".5" patternContentUnits="objectBoundingBox">
        <circle cx=".125" cy=".25" r=".075" fill="red"/>
      </pattern>
      <pattern id="stroke" patternUnits="userSpaceOnUse" width="12" height="12">
        <rect width="6" height="6" fill="red"/>
      </pattern></defs>
      <g fill="url(#p)">
        <rect x="10" y="10" width="80" height="80"/>
        <rect x="110" y="10" width="160" height="80" fill="inherit"/>
        <g transform="translate(0 100)" fill="inherit">
          <rect x="10" y="10" width="80" height="80" fill="blue"/>
          <rect x="110" y="10" width="80" height="80" fill="none"
                stroke="url(#stroke)" stroke-width="8"/>
          <path d="M220 90 L270 90 L245 10 Z"/>
        </g>
      </g>
    </svg>"""
    pdf = FPDF(unit="pt", format=(320, 270))
    pdf.add_page()
    pdf.set_font("helvetica", size=13)
    pdf.text(20, 25, "Inherited patterns use each shape's bounds")
    pdf.image(svg.encode(), x=20, y=40, w=280, h=200)
    assert_svg_golden(pdf, "tiling_inherited_shape_bounds.pdf", tmp_path)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    widths = {
        pattern.get_object()["/Matrix"][0]
        for pattern in page["/Resources"]["/Pattern"].values()
        if pattern.get_object()["/XStep"] == 0.25
    }
    assert widths == {50, 80, 160}


def test_root_pattern_override_and_forward_gradients(tmp_path):
    """Root paint inheritance neither introduces false cycles nor loses defs."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="url(#p)">
      <defs>
        <pattern id="p" fill="black" patternUnits="userSpaceOnUse" width="20" height="20">
          <rect width="20" height="20" fill="url(#g)"/>
          <circle cx="10" cy="10" r="5" fill="none" stroke="black"/>
        </pattern>
        <linearGradient id="g"><stop offset="0" stop-color="red"/>
          <stop offset="1" stop-color="blue"/></linearGradient>
      </defs>
      <rect x="5" y="5" width="50" height="50"/>
      <g><circle cx="90" cy="30" r="25"/></g>
      <rect x="5" y="65" width="110" height="50"/>
    </svg>"""
    pdf = FPDF(unit="pt", format=(280, 300))
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.text(20, 25, "Root pattern, own fill, forward gradient")
    pdf.image(svg.encode(), x=20, y=40, w=240, h=240)
    assert_svg_golden(pdf, "tiling_root_paint_forward_gradient.pdf", tmp_path)
    page = PdfReader(BytesIO(pdf.output())).pages[0]
    for tile in page["/Resources"]["/Pattern"].values():
        nested = tile.get_object()["/Resources"]["/Pattern"]
        assert all(
            pattern.get_object()["/PatternType"] == 2 for pattern in nested.values()
        )


def test_nested_pattern_own_fill_overrides_inherited_url(tmp_path):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="url(#p)">
      <defs><pattern id="p" fill="black" patternUnits="userSpaceOnUse" width="20" height="20">
        <rect x="2" y="2" width="16" height="16"/>
      </pattern></defs><rect width="120" height="120"/>
    </svg>"""
    assert_svg_golden(render_svg(svg), "tiling_root_own_fill_override.pdf", tmp_path)


@pytest.mark.parametrize(
    "gradient_attr,pattern_attr", [("fill", "stroke"), ("stroke", "fill")]
)
def test_mixed_paints_keep_independent_coordinate_systems(gradient_attr, pattern_attr):
    """Changing the other paint must not change a transformed gradient's bounds."""
    matrices = []
    for other_paint in ("black", "url(#p)"):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
          <defs><linearGradient id="g"><stop offset="0" stop-color="red"/>
            <stop offset="1" stop-color="blue"/></linearGradient>
          <pattern id="p" patternUnits="userSpaceOnUse" width="10" height="10">
            <rect width="10" height="10"/></pattern></defs>
          <rect x="10" y="10" width="40" height="40" transform="scale(2)"
            {gradient_attr}="url(#g)" {pattern_attr}="{other_paint}"/>
        </svg>"""
        patterns = patterns_in(render_svg(svg))
        gradient = next(p for p in patterns if p["/PatternType"] == 2)
        matrices.append(list(gradient["/Matrix"]))
    assert matrices == [[80, 0, 0, -80, 20, 100]] * 2


@pytest.mark.parametrize("attr", ["fill", "stroke"])
@pytest.mark.parametrize("placement", ["group", "use", "css", "inherit"])
def test_use_patterns_resolve_per_leaf_and_preserve_overrides(attr, placement):
    group_style = f'{attr}="url(#p)"' if placement in ("group", "inherit") else ""
    use_style = {
        "group": "",
        "use": f'{attr}="url(#p)"',
        "css": f'style="{attr}:url(#p)"',
        "inherit": f'{attr}="inherit"',
    }[placement]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
      <defs><pattern id="p" width=".25" height=".25"
        patternContentUnits="objectBoundingBox">
        <rect width=".1" height=".1" fill="red"/></pattern>
      <g id="shapes">
        <rect width="20" height="20"/>
        <g><rect x="30" width="40" height="20"/></g>
        <rect y="30" width="60" height="20" {attr}="blue"/>
        <rect y="60" width="80" height="20" {attr}="none"/>
      </g></defs>
      <g {group_style}><use xmlns:xlink="http://www.w3.org/1999/xlink"
        xlink:href="#shapes" x="5" y="5" {use_style}/></g>
      <use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#shapes"/>
    </svg>"""
    pdf = render_svg(svg)
    patterns = patterns_in(pdf)
    assert sorted(p["/Matrix"][0] for p in patterns) == [20, 40]
    assert {p["/Matrix"][4] for p in patterns} == {5, 35}
    reader = PdfReader(BytesIO(pdf.output()))
    content = reader.pages[0].get_contents().get_data()
    # Binding one instance must not change the shared reference or other instances.
    assert content.count(b"scn" if attr == "fill" else b"SCN") == 2
    assert content.count(b"0 0 1 rg" if attr == "fill" else b"0 0 1 RG") == 2
