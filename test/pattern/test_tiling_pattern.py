"""Structural and rendered checks for reusable colored tiling patterns."""

# pylint: disable=protected-access,no-member
# Pypdf page/resource dictionaries are dynamic; structural tests inspect internals.
from io import BytesIO
import math
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream

from fpdf import FPDF
from fpdf.errors import FPDFException
from fpdf.drawing import (
    GradientPaint,
    GraphicsContext,
    GraphicsStyle,
    PaintBlendComposite,
    PaintedPath,
    Text,
    TextRun,
)
from fpdf.drawing_primitives import DeviceCMYK, DeviceGray, Transform
from fpdf.pattern import LinearGradient, Pattern
from fpdf.enums import BlendMode, PDFResourceType
from fpdf.svg import SVGObject

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def make_tile(pdf, **kwargs):
    with pdf.create_pattern(10, 10, **kwargs) as tile:
        motif = PaintedPath().rectangle(0, 0, 4, 3)
        motif.style.fill_color = "#ff0000"
        motif.style.stroke_color = None
        tile.add_item(motif)
    return tile


def read_pdf(pdf):
    return PdfReader(BytesIO(pdf.output()))


def test_tile_dictionary_and_resources():
    pdf = FPDF(unit="pt")
    with pdf.create_pattern(10, 12, x_step=15, y_step=18) as tile:
        motif = PaintedPath().rectangle(-2, -2, 6, 6)
        motif.style.fill_color = "#ff0000"
        motif.style.fill_opacity = 0.5
        tile.add_item(motif)
    pdf.add_page()
    with pdf.use_pattern(tile):
        pdf.rect(20, 20, 60, 60, style="F")
    pattern = next(
        iter(read_pdf(pdf).pages[0]["/Resources"]["/Pattern"].values())
    ).get_object()
    assert pattern["/PatternType"] == 1
    assert pattern["/PaintType"] == 1
    assert pattern["/BBox"] == [0, 0, 10, 12]
    assert pattern["/XStep"] == 15
    assert pattern["/YStep"] == 18
    assert pattern["/Resources"]["/ExtGState"]
    assert b" re" in pattern.get_data()


@pytest.mark.parametrize("drawing", [False, True])
def test_rendered_orientation_spacing_and_page_reuse(tmp_path, drawing):
    pdf = FPDF(unit="pt", format=(100, 100))
    tile = make_tile(pdf, x_step=12, y_step=14)
    for height in (100, 120):
        pdf.add_page(format=(100, height))
        if drawing:
            shape = PaintedPath().rectangle(0, 0, 80, 80)
            shape.style.fill_color = tile
            shape.style.stroke_color = None
            with pdf.drawing_context() as context:
                context.add_item(shape)
        else:
            with pdf.use_pattern(tile):
                pdf.rect(0, 0, 80, 80, style="F")
    name = "drawing" if drawing else "use_pattern"
    assert_pdf_equal(pdf, HERE / f"tiling_orientation_{name}.pdf", tmp_path)


def test_pattern_lifecycle_and_document_ownership():
    pdf = FPDF()
    with pdf.create_pattern(10, 10) as tile:
        with pytest.raises(RuntimeError, match="finish"):
            tile.emit_fill(pdf._resource_catalog)
    with pytest.raises(RuntimeError, match="finalized"):
        tile.add_item(PaintedPath())
    other = FPDF()
    other.add_page()
    with pytest.raises(ValueError, match="another document"):
        with other.use_pattern(tile):
            pass


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_pattern_dimensions(value):
    with pytest.raises(ValueError, match="positive"):
        with FPDF().create_pattern(value, 10):
            pass


def test_nested_patterns_and_transform():
    pdf = FPDF(unit="pt")
    inner = make_tile(pdf)
    with pdf.create_pattern(20, 20, transform=Transform.translation(3, 5)) as outer:
        shape = PaintedPath().rectangle(0, 0, 20, 20)
        shape.style.fill_color = inner
        outer.add_item(shape)
    pdf.add_page()
    with pdf.use_pattern(outer):
        pdf.rect(0, 0, 100, 100, style="F")
    reader = read_pdf(pdf)
    pattern = next(
        iter(reader.pages[0]["/Resources"]["/Pattern"].values())
    ).get_object()
    nested = next(iter(pattern["/Resources"]["/Pattern"].values())).get_object()
    assert nested["/PatternType"] == 1
    assert nested["/Matrix"] == [1, 0, 0, 1, 0, 0]


def test_gradient_inside_tile():

    pdf = FPDF(unit="pt")
    with pdf.create_pattern(10, 10) as tile:
        shape = PaintedPath().rectangle(0, 0, 10, 10)
        shape.style.fill_color = GradientPaint(
            LinearGradient(0, 0, 10, 0, ["#ff0000", "#0000ff"])
        )
        tile.add_item(shape)
    pdf.add_page()
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 100, 100, style="F")
    reader = read_pdf(pdf)
    pattern = next(
        iter(reader.pages[0]["/Resources"]["/Pattern"].values())
    ).get_object()
    nested = next(iter(pattern["/Resources"]["/Pattern"].values())).get_object()
    assert nested["/PatternType"] == 2
    assert nested["/Matrix"] == [1, 0, 0, 1, 0, 0]


def test_pattern_stroke_reuse_and_state_restoration():
    pdf = FPDF(unit="pt")
    tile = make_tile(pdf)
    pdf.add_page()
    original = pdf.fill_color
    with pytest.raises(RuntimeError, match="intentional"):
        with pdf.use_pattern(tile):
            pdf.set_fill_color(255, 0, 0)
            raise RuntimeError("intentional")
    assert pdf.fill_color == original
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 30, 30, style="F")
    shape = PaintedPath().rectangle(40, 40, 30, 30)
    shape.style.stroke_color = tile
    shape.style.fill_color = None
    shape.style.stroke_width = 5
    with pdf.drawing_context() as drawing:
        drawing.add_item(shape)
    page = read_pdf(pdf).pages[0]
    assert len(page["/Resources"]["/Pattern"]) == 1
    assert b"SCN" in page.get_contents().get_data()


def test_text_and_image_resources_in_tile(tmp_path):

    image_path = tmp_path / "motif.png"
    Image.new("RGB", (2, 2), "blue").save(image_path)
    pdf = FPDF(unit="pt")
    pdf.set_font("helvetica", size=8)
    svg = SVGObject(
        f'<svg xmlns="http://www.w3.org/2000/svg"><image href="{image_path}" '
        'x="0" y="0" width="3" height="3"/></svg>',
        image_cache=pdf.image_cache,
    )
    group = GraphicsContext()
    group.add_item(Text(0, 9, (TextRun("A", "helvetica", "", 8),)))
    with pdf.create_pattern(10, 10) as tile:
        tile.add_item(group)
        tile.add_item(svg.base_group)
    pdf.add_page()
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 100, 100, style="F")
    page = read_pdf(pdf).pages[0]
    pattern = next(iter(page["/Resources"]["/Pattern"].values())).get_object()
    assert pattern["/Resources"]["/Font"]["/F1"]["/BaseFont"] == "/Helvetica"
    assert pattern["/Resources"]["/XObject"]["/I1"]["/Subtype"] == "/Image"
    assert "/Font" not in page["/Resources"]
    assert "/XObject" not in page["/Resources"]


@pytest.mark.parametrize("encrypted", [False, True])
def test_unified_pattern_serialization(encrypted):

    pdf = FPDF(unit="pt")
    tile = make_tile(pdf)
    gradient = LinearGradient(0, 0, 10, 0, ["#ff0000", "#0000ff"])
    assert Pattern.from_shading(gradient).content_stream() is None
    pdf.add_page()
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 30, 30, style="F")
    with pdf.use_pattern(gradient):
        pdf.rect(40, 40, 30, 30, style="F")
    assert all(
        isinstance(pattern, Pattern)
        for pattern, _ in pdf._resource_catalog.get_items(PDFResourceType.PATTERN)
    )
    if encrypted:
        pdf.set_encryption(owner_password="secret")
    reader = read_pdf(pdf)
    if encrypted:
        assert reader.decrypt("secret")
    patterns = [
        ref.get_object() for ref in reader.pages[0]["/Resources"]["/Pattern"].values()
    ]
    shading = next(pattern for pattern in patterns if pattern["/PatternType"] == 2)
    tiling = next(pattern for pattern in patterns if pattern["/PatternType"] == 1)
    assert "/Shading" in shading
    for field in ("/Length", "/Filter", "/PaintType", "/BBox", "/Resources"):
        assert field not in shading
    assert "/Shading" not in tiling
    assert tiling["/Filter"] == "/FlateDecode"
    assert tiling.get_data().startswith(b"q ")
    assert tiling["/Resources"]


def test_six_tiling_patterns(tmp_path):
    """A visual reference page covering six motifs and both application APIs."""
    pdf = FPDF(unit="pt", format=(440, 680))

    def add_motif(tile, path, color):
        path.style.fill_color = color
        path.style.stroke_color = None
        tile.add_item(path)

    with pdf.create_pattern(12, 12) as stripes:
        add_motif(stripes, PaintedPath().rectangle(0, 0, 5, 12), "#167D8D")

    with pdf.create_pattern(16, 16) as dots:
        add_motif(dots, PaintedPath().circle(8, 8, 3), "#C04B68")

    with pdf.create_pattern(16, 16) as checkerboard:
        add_motif(checkerboard, PaintedPath().rectangle(0, 0, 8, 8), "#36445C")
        add_motif(checkerboard, PaintedPath().rectangle(8, 8, 8, 8), "#36445C")

    with pdf.create_pattern(
        12, 12, transform=Transform.rotation(math.pi / 4)
    ) as diagonal:
        add_motif(diagonal, PaintedPath().rectangle(0, 0, 4, 12), "#D28B26")

    with pdf.create_pattern(18, 18) as crosses:
        add_motif(crosses, PaintedPath().rectangle(7, 3, 4, 12), "#50804B")
        add_motif(crosses, PaintedPath().rectangle(3, 7, 12, 4), "#50804B")

    with pdf.create_pattern(18, 18, x_step=22, y_step=22) as gradient_tiles:
        add_motif(
            gradient_tiles,
            PaintedPath().rectangle(0, 0, 18, 18),
            GradientPaint(LinearGradient(0, 0, 18, 18, ["#5968D8", "#BF64B5"])),
        )

    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.text(32, 26, "Six tiling patterns")
    pdf.set_draw_color(100)
    pdf.set_line_width(0.5)
    patterns = (
        ("Stripes", stripes),
        ("Dots", dots),
        ("Checkerboard", checkerboard),
        ("Diagonal stripes", diagonal),
        ("Crosses", crosses),
        ("Gradient tiles", gradient_tiles),
    )
    for index, (label, pattern) in enumerate(patterns):
        x = 32 + (index % 2) * 216
        y = 50 + (index // 2) * 210
        if index % 2 == 0:
            with pdf.use_pattern(pattern):
                pdf.rect(x, y, 160, 160, style="F")
        else:
            square = PaintedPath().rectangle(x, y, 160, 160)
            square.style.fill_color = pattern
            square.style.stroke_color = None
            with pdf.drawing_context() as drawing:
                drawing.add_item(square)
        pdf.rect(x, y, 160, 160)
        pdf.set_font("helvetica", size=11)
        pdf.text(x, y + 177, label)

    assert_pdf_equal(pdf, HERE / "tiling_six_patterns.pdf", tmp_path)


def test_text_tile_fills_square_and_circle(tmp_path):
    """Text in a tile uses the tile's font resources and clips to each shape."""
    pdf = FPDF(unit="pt", format=(520, 340))
    with pdf.create_pattern(48, 20) as tile:
        word = PaintedPath()
        word.add_path_element(Text(3, 14, (TextRun("fpdf2", "helvetica", "B", 12),)))
        word.style.fill_color = "#167D8D"
        word.style.stroke_color = None
        tile.add_item(word)

    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.text(30, 28, 'Shapes filled with an "fpdf2" text tile')

    with pdf.use_pattern(tile):
        pdf.rect(30, 65, 210, 210, style="F")

    circle = PaintedPath().circle(390, 170, 105)
    circle.style.fill_color = tile
    circle.style.stroke_color = None
    with pdf.drawing_context() as drawing:
        drawing.add_item(circle)

    pdf.set_draw_color(100)
    pdf.set_line_width(0.5)
    pdf.rect(30, 65, 210, 210)
    outline = PaintedPath().circle(390, 170, 105)
    outline.style.fill_color = None
    with pdf.drawing_context() as drawing:
        drawing.add_item(outline)
    pdf.set_font("helvetica", size=11)
    pdf.text(30, 300, "Square - use_pattern()")
    pdf.text(285, 300, "Circle - drawing style")

    assert_pdf_equal(pdf, HERE / "tiling_text_in_shapes.pdf", tmp_path)


def test_text_filled_with_tiling_patterns(tmp_path):
    """Pattern paints fill glyphs through both path and explicit text-run styles."""
    pdf = FPDF(unit="pt", format=(520, 430))
    with pdf.create_pattern(8, 8, transform=Transform.rotation(math.pi / 4)) as stripes:
        stripe = PaintedPath().rectangle(0, 0, 4, 8)
        stripe.style.fill_color = "#167D8D"
        stripe.style.stroke_color = None
        stripes.add_item(stripe)

    with pdf.create_pattern(10, 10) as checkerboard:
        for x, y in ((0, 0), (5, 5)):
            square = PaintedPath().rectangle(x, y, 5, 5)
            square.style.fill_color = "#5968D8"
            square.style.stroke_color = None
            checkerboard.add_item(square)

    with pdf.create_pattern(9, 9) as dots:
        dot = PaintedPath().circle(4.5, 4.5, 2.8)
        dot.style.fill_color = "#C04B68"
        dot.style.stroke_color = None
        dots.add_item(dot)

    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.text(30, 28, "Text filled with tiling patterns")
    for index, (label, pattern) in enumerate(
        (("Diagonal stripes", stripes), ("Checkerboard", checkerboard), ("Dots", dots))
    ):
        baseline = 148 + index * 125
        pdf.set_font("helvetica", size=11)
        pdf.text(30, baseline - 90, label)
        word = PaintedPath()
        run_style = None
        if index == 2:
            run_style = GraphicsStyle()
            run_style.fill_color = pattern
            run_style.stroke_color = None
        word.add_path_element(
            Text(
                30,
                baseline,
                (TextRun("fpdf2", "helvetica", "B", 112, run_style=run_style),),
            )
        )
        word.style.fill_color = pattern
        word.style.stroke_color = None
        with pdf.drawing_context() as drawing:
            drawing.add_item(word)

    assert_pdf_equal(pdf, HERE / "text_fill_tiling_patterns.pdf", tmp_path)


def test_uncolored_tile_color_binding_and_resources():

    pdf = FPDF(unit="pt", format=(240, 120))
    pdf.set_fill_color(0, 0, 255)  # Must not enter the stencil's stream.
    with pdf.create_pattern(10, 10, colored=False) as tile:
        motif = PaintedPath().rectangle(0, 0, 4, 4)
        motif.style.stroke_color = None
        tile.add_item(motif)
    pdf.add_page()
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 40, 40, style="F")
    for index, color in enumerate(("#ff0000", DeviceGray(0.5), DeviceCMYK(1, 0, 0, 0))):
        shape = PaintedPath().rectangle(50 + index * 50, 0, 40, 40)
        shape.style.fill_color = tile.with_color(color)
        shape.style.stroke_color = None
        with pdf.drawing_context() as drawing:
            drawing.add_item(shape)
    reader = read_pdf(pdf)
    page = reader.pages[0]
    assert len(page["/Resources"]["/Pattern"]) == 1
    pattern = next(iter(page["/Resources"]["/Pattern"].values())).get_object()
    assert pattern["/PaintType"] == 2
    assert not {op for _, op in ContentStream(pattern, reader).operations} & {
        b"rg",
        b"RG",
        b"g",
        b"G",
        b"k",
        b"K",
        b"cs",
        b"CS",
        b"scn",
        b"SCN",
    }
    spaces = page["/Resources"]["/ColorSpace"]
    for base in ("DeviceRGB", "DeviceGray", "DeviceCMYK"):
        assert spaces["/PCS" + base] == ["/Pattern", "/" + base]
    assert b"0 0 1 /P1 scn" in page.get_contents().get_data()
    assert b"1 0 0 /P1 scn" in page.get_contents().get_data()
    with pytest.raises(ValueError, match="with_color"):
        tile.emit_fill(pdf._resource_catalog)
    with pytest.raises(ValueError, match="uncolored"):
        make_tile(FPDF()).with_color("#ff0000")


@pytest.mark.parametrize(
    "paint",
    ["#ff0000", GradientPaint(LinearGradient(0, 0, 10, 0, ["#ff0000", "#0000ff"]))],
)
def test_uncolored_tile_rejects_explicit_paints(paint):
    pdf = FPDF()
    with pytest.raises(ValueError, match="explicit"):
        with pdf.create_pattern(10, 10, colored=False) as tile:
            shape = PaintedPath().rectangle(0, 0, 5, 5)
            shape.style.fill_color = paint
            tile.add_item(shape)
    assert not pdf._resource_catalog.uncolored_pattern


def test_uncolored_tile_rejects_images(tmp_path):

    image = tmp_path / "motif.png"
    Image.new("RGB", (2, 2), "red").save(image)
    pdf = FPDF()
    svg = SVGObject(
        f'<svg xmlns="http://www.w3.org/2000/svg"><image href="{image}" width="4" height="4"/></svg>',
        image_cache=pdf.image_cache,
    )
    with pytest.raises(ValueError, match="ordinary images"):
        with pdf.create_pattern(10, 10, colored=False) as tile:
            tile.add_item(svg.base_group)


def testuncolored_patterns_golden(tmp_path):
    pdf = FPDF(unit="pt", format=(500, 400))
    with pdf.create_pattern(12, 12, colored=False) as tile:
        motif = PaintedPath().circle(6, 6, 3)
        motif.style.stroke_color = None
        tile.add_item(motif)
    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.text(30, 28, "One uncolored tile, different colors")
    for index, color in enumerate(((22, 125, 141), (192, 75, 104))):
        pdf.set_fill_color(*color)
        with pdf.use_pattern(tile):
            pdf.rect(30 + index * 240, 60, 200, 140, style="F")
    shape = PaintedPath().circle(120, 290, 70)
    shape.style.fill_color = tile.with_color("#5968D8")
    shape.style.stroke_color = tile.with_color("#C04B68")
    shape.style.stroke_width = 10
    word = PaintedPath()
    word.add_path_element(Text(250, 315, (TextRun("fpdf2", "helvetica", "B", 72),)))
    word.style.fill_color = tile.with_color("#50804B")
    word.style.stroke_color = None
    with pdf.drawing_context() as drawing:
        drawing.add_item(shape)
        drawing.add_item(word)
    assert_pdf_equal(pdf, HERE / "tiling_uncolored.pdf", tmp_path)


def testuncolored_pattern_inside_isolated_blend():

    pdf = FPDF(unit="pt")
    with pdf.create_pattern(10, 10, colored=False) as tile:
        motif = PaintedPath().rectangle(0, 0, 4, 4)
        motif.style.stroke_color = None
        tile.add_item(motif)
    pdf.add_page()
    backdrop = PaintedPath().rectangle(20, 20, 50, 50)
    backdrop.style.fill_color = "#ffffff"
    backdrop.style.stroke_color = None
    source = PaintedPath().rectangle(20, 20, 50, 50)
    source.style.fill_color = tile.with_color("#ff0000")
    source.style.stroke_color = None
    group = GraphicsContext()
    group.add_item(PaintBlendComposite(backdrop, source, BlendMode.MULTIPLY))
    with pdf.drawing_context() as drawing:
        drawing.add_item(group)
    page = read_pdf(pdf).pages[0]
    form = next(iter(page["/Resources"]["/XObject"].values())).get_object()
    assert form["/Resources"]["/ColorSpace"]["/PCSDeviceRGB"] == [
        "/Pattern",
        "/DeviceRGB",
    ]
    assert form["/Resources"]["/Pattern"]


def test_uncolored_text_tile():

    pdf = FPDF(unit="pt")
    with pdf.create_pattern(48, 20, colored=False) as tile:
        word = PaintedPath()
        word.add_path_element(Text(3, 14, (TextRun("fpdf2", "helvetica", "B", 12),)))
        word.style.stroke_color = None
        tile.add_item(word)
    pdf.add_page()
    pdf.set_fill_color(255, 0, 0)
    with pdf.use_pattern(tile):
        pdf.rect(0, 0, 100, 100, style="F")
    reader = read_pdf(pdf)
    pattern = next(
        iter(reader.pages[0]["/Resources"]["/Pattern"].values())
    ).get_object()
    ops = {op for _, op in ContentStream(pattern, reader).operations}
    assert b"Tj" in ops
    assert not ops & {b"rg", b"RG", b"g", b"G", b"k", b"K"}
    assert pattern["/Resources"]["/Font"]


def test_colored_tile_captures_creation_defaults(tmp_path):
    """A tile snapshots fill/stroke colors and width when creation starts."""
    pdf = FPDF(unit="pt", format=(320, 220))
    pdf.set_fill_color(255, 0, 0)
    pdf.set_draw_color(0, 0, 255)
    pdf.set_line_width(3)
    with pdf.create_pattern(24, 24) as tile:
        tile.add_item(PaintedPath().circle(12, 12, 8))
        # Later changes must not recolor or restyle the tile's inherited paints.
        pdf.set_fill_color(0, 180, 0)
        pdf.set_draw_color(0, 180, 0)
        pdf.set_line_width(1)
    pdf.add_page()
    pdf.set_font("helvetica", size=14)
    pdf.text(20, 25, "Captured red fill and blue stroke")
    with pdf.use_pattern(tile):
        pdf.rect(20, 45, 120, 120, style="F")
    square = PaintedPath().rectangle(160, 45, 120, 120)
    square.style.fill_color = tile
    square.style.stroke_color = None
    with pdf.drawing_context() as drawing:
        drawing.add_item(square)
    pdf.set_font("helvetica", size=11)
    pdf.text(20, 183, "use_pattern()")
    pdf.text(160, 183, "Drawing style")
    pdf.rect(20, 195, 260, 10, style="F")
    assert_pdf_equal(pdf, HERE / "tiling_captured_defaults.pdf", tmp_path)
    page = read_pdf(pdf).pages[0]
    pattern = next(iter(page["/Resources"]["/Pattern"].values())).get_object()
    assert b"1 0 0 rg" in pattern.get_data()
    assert b"0 0 1 RG" in pattern.get_data()
    assert any(
        state.get_object().get("/LW") == 3
        for state in pattern["/Resources"]["/ExtGState"].values()
    )


def test_tiling_pattern_page_scope(tmp_path):
    """Rejected page breaks leave the state valid; the tile is reusable later."""
    pdf = FPDF(unit="pt", format=(240, 240))
    pdf.set_auto_page_break(True, margin=20)
    tile = make_tile(pdf)
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.text(15, 25, "Rejected manual and automatic breaks")
    with pdf.use_pattern(tile):
        with pytest.raises(FPDFException, match="Finish use_pattern"):
            pdf.add_page()
        pdf.set_y(pdf.h - pdf.b_margin - 1)
        with pytest.raises(FPDFException, match="Finish use_pattern"):
            pdf.cell(w=20, h=5)
        assert pdf.page == 1
        pdf.set_xy(20, 60)
        pdf.rect(20, 60, 200, 120, style="F")
    pdf.add_page()
    pdf.text(15, 25, "Reuse after finishing the context")
    with pdf.use_pattern(tile):
        pdf.rect(20, 60, 200, 120, style="F")
    assert_pdf_equal(pdf, HERE / "tiling_page_scope.pdf", tmp_path)
    reader = read_pdf(pdf)
    assert len(reader.pages) == 2
    for page in reader.pages:
        assert page["/Resources"]["/Pattern"]
        depth = 0
        for _, operator in ContentStream(page.get_contents(), reader).operations:
            if operator == b"q":
                depth += 1
            elif operator == b"Q":
                depth -= 1
                assert depth >= 0
        assert depth == 0
