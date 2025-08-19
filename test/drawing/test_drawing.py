# pylint: disable=no-self-use, protected-access, redefined-outer-name, unused-argument

import copy
import io
import math
from pathlib import Path
import re

from fpdf.enums import (
    BlendMode,
    IntersectionRule,
    PathPaintRule,
    StrokeCapStyle,
    StrokeJoinStyle,
)
from fpdf.errors import FPDFException
from fpdf.fpdf import FPDF
from fpdf.output import ResourceCatalog
from fpdf.syntax import Name
from test.conftest import assert_pdf_equal
from fpdf.drawing import (
    ClippingPath,
    DrawingContext,
    GraphicsContext,
    GraphicsStyle,
    ImplicitClose,
    Line,
    Move,
    PaintedPath,
    RelativeLine,
    render_pdf_primitive,
)
from fpdf.drawing_primitives import (
    DeviceCMYK,
    DeviceGray,
    DeviceRGB,
    Point,
    Transform,
    check_range,
    cmyk8,
    color_from_hex_string,
    color_from_rgb_string,
    gray8,
    number_to_str,
    rgb8,
)

import pytest

from . import parameters


HERE = Path(__file__).resolve().parent
bad_path_chars = re.compile(r"[\[\]=#, ]")


@pytest.fixture(scope="function")
def auto_pdf(request):
    pdf = FPDF(unit="mm", format=(10, 10))
    pdf.add_page()

    yield pdf


@pytest.fixture(scope="function")
def auto_pdf_cmp(request, tmp_path, auto_pdf):
    yield auto_pdf

    assert_pdf_equal(
        auto_pdf,
        HERE / "generated_pdf" / f"{bad_path_chars.sub('_', request.node.name)}.pdf",
        tmp_path,
    )


@pytest.fixture
def open_path_drawing():
    path = PaintedPath()
    path.move_to(2, 2)
    path.curve_to(4, 3, 6, 3, 8, 2)
    path.line_to(8, 8)
    path.curve_to(6, 7, 4, 7, 2, 8)

    path.style.fill_color = "#CCCF"
    path.style.stroke_color = "#333F"
    path.style.stroke_width = 0.5
    path.style.stroke_cap_style = "round"
    path.style.stroke_join_style = "round"
    path.style.auto_close = False

    return path


@pytest.fixture
def prepared_blend_path(open_path_drawing):
    open_path_drawing.style.fill_color = rgb8(100, 120, 200)
    open_path_drawing.style.stroke_color = rgb8(200, 120, 100)
    open_path_drawing.style.fill_opacity = 0.8
    open_path_drawing.style.stroke_opacity = 0.8

    return open_path_drawing


class TestUtilities:
    def test_range_check(self):
        with pytest.raises(ValueError):
            check_range(-1, minimum=0.0, maximum=0.0)

        check_range(0, minimum=0.0, maximum=1.0)
        check_range(1, minimum=0.0, maximum=1.0)

    @pytest.mark.parametrize("number, converted", parameters.numbers)
    def test_number_to_str(self, number, converted):
        assert number_to_str(number) == converted

    @pytest.mark.parametrize("primitive, result", parameters.pdf_primitives)
    def test_render_primitive(self, primitive, result):
        assert render_pdf_primitive(primitive) == result

    # Add check for bad primitives: class without serialize, dict with non-Name
    # keys. Check for proper escaping of Name and string edge cases
    @pytest.mark.parametrize("primitive, error_type", parameters.pdf_bad_primitives)
    def test_error_on_bad_primitive(self, primitive, error_type):
        with pytest.raises(error_type):
            render_pdf_primitive(primitive)


class TestGraphicsStateDictRegistry:
    @pytest.fixture
    def new_style_registry(self):
        return ResourceCatalog()

    def test_empty_style(self, new_style_registry):
        style = GraphicsStyle()

        result = new_style_registry.register_graphics_style(style)

        assert result is None

    def test_adding_styles(self, new_style_registry):
        first = GraphicsStyle()
        second = GraphicsStyle()

        first.stroke_width = 1
        second.stroke_width = 2

        first_name = new_style_registry.register_graphics_style(first)
        second_name = new_style_registry.register_graphics_style(second)

        assert isinstance(first_name, Name)
        assert isinstance(second_name, Name)
        assert first_name != second_name
        # I don't think it's necessary to check that first_name is actually e.g. "GS1", since
        # the naming pattern is an implementation detail that can change without
        # affecting anything.

    def test_style_deduplication(self, new_style_registry):
        first = GraphicsStyle()
        second = GraphicsStyle()

        first.stroke_width = 1
        second.stroke_width = 1

        first_name = new_style_registry.register_graphics_style(first)
        second_name = new_style_registry.register_graphics_style(second)

        assert isinstance(first_name, Name)
        assert isinstance(second_name, Name)
        assert first_name == second_name


class TestColors:
    def test_device_rgb(self):
        rgb = DeviceRGB(r=1, g=0.5, b=0.25)
        rgba = DeviceRGB(r=1, g=0.5, b=0.25, a=0.75)

        assert rgb.colors == (1, 0.5, 0.25)
        assert rgba.colors == (1, 0.5, 0.25)

        with pytest.raises(ValueError):
            DeviceRGB(r=2, g=1, b=0)

    def test_device_gray(self):
        gray = DeviceGray(g=0.5)
        gray_a = DeviceGray(g=0.5, a=0.75)

        assert gray.colors == (0.5, 0.5, 0.5)
        assert gray_a.colors == (0.5, 0.5, 0.5)

        with pytest.raises(ValueError):
            DeviceGray(g=2)

    def test_device_cmyk(self):
        cmyk = DeviceCMYK(c=1, m=1, y=1, k=0)
        cmyk_a = DeviceCMYK(c=1, m=1, y=1, k=0, a=0.5)

        assert cmyk.colors == (1, 1, 1, 0)
        assert cmyk_a.colors == (1, 1, 1, 0)

        assert cmyk.serialize() == "1 1 1 0 k"
        assert cmyk_a.serialize() == "1 1 1 0 k"

        with pytest.raises(ValueError):
            DeviceCMYK(c=2, m=1, y=1, k=0)

    def test_rgb8(self):
        rgb = rgb8(255, 254, 253)
        rgba = rgb8(r=255, g=254, b=253, a=252)

        assert rgb == DeviceRGB(r=1.0, g=254 / 255, b=253 / 255)
        assert rgba == DeviceRGB(r=1.0, g=254 / 255, b=253 / 255, a=252 / 255)

    def test_gray8(self):
        gray = gray8(255)
        gray_a = gray8(g=255, a=254)

        assert gray == DeviceGray(g=1.0)
        assert gray_a == DeviceGray(g=1.0, a=254 / 255)

    def test_cmyk8(self):
        cmyk = cmyk8(255, 254, 253, 252)
        cmyk_a = cmyk8(c=255, m=254, y=253, k=252, a=251)

        assert cmyk == DeviceCMYK(c=1.0, m=254 / 255, y=253 / 255, k=252 / 255)
        assert cmyk_a == DeviceCMYK(
            c=1.0, m=254 / 255, y=253 / 255, k=252 / 255, a=251 / 255
        )

    @pytest.mark.parametrize("hex_string, result", parameters.hex_colors)
    def test_hex_string_parser(self, hex_string, result):
        if isinstance(result, type) and issubclass(result, Exception):
            with pytest.raises(result):
                color_from_hex_string(hex_string)
        else:
            assert color_from_hex_string(hex_string) == result

    @pytest.mark.parametrize("rgb_string, result", parameters.rgb_colors)
    def test_rgb_string_parser(self, rgb_string, result):
        if isinstance(result, type) and issubclass(result, Exception):
            with pytest.raises(result):
                color_from_rgb_string(rgb_string)
        else:
            assert color_from_rgb_string(rgb_string) == result


class TestPoint:
    def test_render(self):
        pt = Point(1, 1)

        assert pt.render() == "1 1"

    def test_dot(self):
        pt1 = Point(1, 2)
        pt2 = Point(3, 4)

        assert pt1.dot(pt2) == 11
        assert pt2.dot(pt1) == 11

        with pytest.raises(TypeError):
            pt1.dot(1)

    def test_angle(self):
        pt1 = Point(1, 0)
        pt2 = Point(0, 1)

        assert pt1.angle(pt2) == pytest.approx(math.pi / 2)
        assert pt2.angle(pt1) == pytest.approx(-(math.pi / 2))

        with pytest.raises(TypeError):
            pt1.angle(1)

    def test_magnitude(self):
        pt1 = Point(2, 0)

        assert pt1.mag() == 2.0

    def test_add(self):
        pt1 = Point(1, 0)
        pt2 = Point(0, 1)

        assert pt1 + pt2 == Point(1, 1)
        assert pt2 + pt1 == Point(1, 1)

        with pytest.raises(TypeError):
            _ = pt1 + 2

    def test_sub(self):
        pt1 = Point(1, 0)
        pt2 = Point(0, 1)

        assert pt1 - pt2 == Point(1, -1)
        assert pt2 - pt1 == Point(-1, 1)

        with pytest.raises(TypeError):
            _ = pt1 - 2

    def test_neg(self):
        pt = Point(1, 2)

        assert -pt == Point(-1, -2)

    def test_mul(self):
        pt = Point(1, 2)

        assert pt * 2 == Point(2, 4)
        assert 2 * pt == Point(2, 4)

        with pytest.raises(TypeError):
            _ = pt * pt

    def test_div(self):
        pt = Point(1, 2)

        assert (pt / 2) == Point(0.5, 1.0)
        assert (pt // 2) == Point(0, 1)

        with pytest.raises(TypeError):
            _ = 2 / pt

        with pytest.raises(TypeError):
            _ = 2 // pt

        with pytest.raises(TypeError):
            _ = pt / pt

        with pytest.raises(TypeError):
            _ = pt // pt

    def test_matmul(self):
        pt = Point(2, 4)
        tf = Transform.translation(2, 2)

        assert pt @ tf == Point(4, 6)

        with pytest.raises(TypeError):
            _ = tf @ pt

        with pytest.raises(TypeError):
            _ = pt @ pt

    def test_str(self):
        pt = Point(2, 4)

        assert str(pt) == "(x=2, y=4)"


class TestTransform:
    @pytest.mark.parametrize("tf, pt, result", parameters.transforms)
    def test_constructors(self, tf, pt, result):
        # use of pytest.approx here works because Point is a NamedTuple
        # (approx supports tuples) and wouldn't work if it were a normal object
        assert pt @ tf == pytest.approx(result)

    def test_chaining(self):
        tf = Transform.identity().translate(1, 1).scale(2, 1).rotate(0.3).shear(0, 0.5)
        assert tf == pytest.approx(
            Transform(
                a=1.910672978251212,
                b=1.546376902448285,
                c=-0.29552020666133955,
                d=0.8075763857949362,
                e=1.6151527715898724,
                f=2.353953288243221,
            )
        )

    def test_about(self):
        tf = Transform.scaling(2).about(10, 10)

        assert tf == Transform(a=2, b=0, c=0, d=2, e=-10, f=-10)
        assert tf == Transform.translation(-10, -10).scale(2).translate(10, 10)

    def test_mul(self):
        tf = Transform(1, 2, 3, 4, 5, 6)

        assert tf * 6 == Transform(6, 12, 18, 24, 30, 36)
        assert 6 * tf == Transform(6, 12, 18, 24, 30, 36)

        with pytest.raises(TypeError):
            _ = tf * "abc"

    def test_matmul(self):
        tf1 = Transform(1, 2, 3, 4, 5, 6)
        tf2 = Transform(6, 5, 4, 3, 2, 1)

        assert tf1 @ tf2 == Transform(a=14, b=11, c=34, d=27, e=56, f=44)
        assert tf2 @ tf1 == Transform(a=21, b=32, c=13, d=20, e=10, f=14)

        with pytest.raises(TypeError):
            _ = tf1 @ 123

    def test_render(self):
        tf = Transform(1, 2, 3, 4, 5, 6)

        assert tf.render(Move(Point(0, 0)))[0] == "1 2 3 4 5 6 cm"

    def test_str(self):
        # don't actually assert the output looks like something in particular, just make
        # sure it doesn't raise, I guess.
        str(Transform(1, 2, 3, 4, 5, 6))


class TestStyleEnums:
    @pytest.mark.parametrize("owner, values, result, guard", parameters.coercive_enums)
    def test_coercive_enums(self, owner, values, result, guard):
        # this is just brute force testing which doesn't seem to be the most intelligent
        # way to do it, but I also don't have a better strategy at all
        for value in values:
            with guard():
                assert owner.coerce(value) is result


class TestStyles:
    @pytest.mark.parametrize("style_name, value", parameters.style_attributes)
    def test_individual_attribute(
        self, auto_pdf_cmp, open_path_drawing, style_name, value
    ):
        setattr(open_path_drawing.style, style_name, value)

        auto_pdf_cmp.draw_path(open_path_drawing)

    def test_stroke_miter_limit(self, auto_pdf_cmp, open_path_drawing):
        open_path_drawing.style.stroke_join_style = "miter"
        open_path_drawing.style.stroke_miter_limit = 1.4

        auto_pdf_cmp.draw_path(open_path_drawing)

    def test_stroke_dash_phase(self, auto_pdf_cmp, open_path_drawing):
        open_path_drawing.style.stroke_dash_pattern = [0.5, 0.5]
        open_path_drawing.style.stroke_dash_phase = 0.5

        auto_pdf_cmp.draw_path(open_path_drawing)

    @pytest.mark.parametrize(
        "blend_mode", parameters.blend_modes, ids=lambda param: f"blend mode {param}"
    )
    def test_blend_modes(
        self, auto_pdf_cmp, open_path_drawing, prepared_blend_path, blend_mode
    ):
        prepared_blend_path.style.blend_mode = blend_mode

        auto_pdf_cmp.draw_path(open_path_drawing)

    def test_serialize_to_pdf_dict(self):
        style = GraphicsStyle()

        style.fill_opacity = 0.5
        style.stroke_opacity = 0.75
        style.blend_mode = "lighten"
        style.stroke_width = 2
        style.stroke_join_style = "round"
        style.stroke_cap_style = "butt"

        assert (
            style.serialize()
            == "<< /Type /ExtGState\n/ca 0.5\n/BM /Lighten\n/CA 0.75\n/LW 2\n/LC 0\n/LJ 1 >>"
        )

    @pytest.mark.parametrize("style_name, value, exception", parameters.invalid_styles)
    def test_bad_style_parameters(self, style_name, value, exception):
        style = GraphicsStyle()
        with pytest.raises(exception):
            setattr(style, style_name, value)

    def test_merge(self):
        style = GraphicsStyle()

        style.fill_opacity = 0.5
        style.stroke_opacity = 0.75
        style.blend_mode = "lighten"
        style.stroke_width = 2
        style.stroke_join_style = "round"
        style.stroke_cap_style = "butt"

        override = GraphicsStyle()

        override.fill_opacity = 0.25
        override.stroke_opacity = 0.1
        override.blend_mode = "hue"

        merged = GraphicsStyle.merge(style, override)

        assert merged.fill_opacity == 0.25
        assert merged.stroke_opacity == 0.1
        assert merged.blend_mode == BlendMode.HUE.value
        assert merged.stroke_width == 2
        assert merged.stroke_join_style == StrokeJoinStyle.ROUND.value
        assert merged.stroke_cap_style == StrokeCapStyle.BUTT.value

    @pytest.mark.parametrize("paint_rule, expected", parameters.paint_rules)
    def test_paint_rule(self, paint_rule, expected):
        style = GraphicsStyle()
        style.paint_rule = paint_rule
        assert style.paint_rule is expected

    def test_paint_rule_resolution(self):
        style = GraphicsStyle()

        style.paint_rule = "auto"

        assert style.resolve_paint_rule() is PathPaintRule.STROKE_FILL_NONZERO

        style.stroke_width = 2
        style.stroke_color = "#000"
        style.fill_color = None
        assert style.resolve_paint_rule() is PathPaintRule.STROKE

        style.fill_color = "#123"
        assert style.resolve_paint_rule() is PathPaintRule.STROKE_FILL_NONZERO

        style.intersection_rule = IntersectionRule.EVENODD
        assert style.resolve_paint_rule() is PathPaintRule.STROKE_FILL_EVENODD

    def test_copy(self):
        style = GraphicsStyle()

        style.fill_opacity = 0.5

        copied = copy.deepcopy(style)

        copied.fill_opacity = 1.0

        assert style is not copied
        assert style.fill_opacity != copied.fill_opacity


def test_path_start_relative():
    """
    Test starting a path with a relative move.
    The parametrized series below can't cover that case.
    """
    point = Point(1, 2)
    start = Move(point)
    element = RelativeLine(Point(3, 4))
    expected = "4 6 l"
    style = GraphicsStyle()
    style.auto_close = False
    rendered, last_item, _ = element.render({}, style, start, point)
    assert rendered == expected
    assert isinstance(last_item, Line)


class TestPathElements:
    @pytest.mark.parametrize(
        "point, element, expected, end_point, end_class", parameters.path_elements
    )
    def test_render(self, point, element, expected, end_point, end_class):
        start = Move(point)
        style = GraphicsStyle()
        style.auto_close = False
        rendered, last_item, _ = element.render({}, style, start, point)

        assert rendered == expected
        assert isinstance(last_item, end_class)
        assert last_item.end_point == pytest.approx(end_point)

    @pytest.mark.parametrize(
        "point, element, expected, end_point, end_class", parameters.path_elements
    )
    def test_render_debug(self, point, element, expected, end_point, end_class):
        start = Move(point)
        dbg = io.StringIO()
        style = GraphicsStyle()
        style.auto_close = False
        rendered, last_item, _ = element.render_debug({}, style, start, point, dbg, "")

        assert rendered == expected
        assert isinstance(last_item, end_class)
        assert last_item.end_point == pytest.approx(end_point)


class TestDrawingContext:
    def test_add_item(self):
        ctx = DrawingContext()

        ctx.add_item(GraphicsContext())

        with pytest.raises(TypeError):
            ctx.add_item(Move(Point(1, 2)))

    def test_empty_render(self):
        ctx = DrawingContext()
        ctx.add_item(GraphicsContext())

        resource_catalog = ResourceCatalog()
        start = Point(0, 0)
        style = GraphicsStyle()

        result = ctx.render(resource_catalog, start, 1, 10, style)

        assert result == ""

    def test_render(self):
        ctx = DrawingContext()
        ctx.add_item(PaintedPath().line_to(10, 10))

        resource_catalog = ResourceCatalog()
        start = Point(0, 0)
        style = GraphicsStyle()

        result = ctx.render(resource_catalog, start, 1, 10, style)

        assert result == "q 1 0 0 -1 0 10 cm q 0 0 m 10 10 l h B Q Q"

    def test_empty_render_debug(self):
        ctx = DrawingContext()
        ctx.add_item(GraphicsContext())

        resource_catalog = ResourceCatalog()
        start = Point(0, 0)
        style = GraphicsStyle()
        dbg = io.StringIO()

        result = ctx.render_debug(resource_catalog, start, 1, 10, style, dbg)

        assert result == ""

    def test_render_debug(self, auto_pdf):
        dbg = io.StringIO()

        with auto_pdf.drawing_context(debug_stream=dbg) as ctx:
            ctx.add_item(PaintedPath().line_to(10, 10))

        assert dbg.getvalue() == (
            "ROOT\n"
            " └─ GraphicsContext {\n"
            "        paint_rule: PathPaintRule.AUTO (inherited)\n"
            "        allow_transparency: True (inherited)\n"
            "        auto_close: True (inherited)\n"
            "        intersection_rule: IntersectionRule.NONZERO (inherited)\n"
            "        stroke_width: 0.20002499999999995 (inherited)\n"
            "        stroke_dash_pattern: () (inherited)\n"
            "        stroke_dash_phase: 0 (inherited)\n"
            "    }┐\n"
            "     ├─ Move(pt=Point(x=0, y=0))\n"
            "     ├─ Line(pt=Point(x=10, y=10))\n"
            "     └─ ImplicitClose() resolved to h\n"
        )

    def test_concurrent_drawing_context(self, auto_pdf):
        with auto_pdf.drawing_context() as _:
            with pytest.raises(FPDFException):
                with auto_pdf.drawing_context() as _:
                    pass


# this is named so it doesn't get picked up by pytest implicitly.
class CommonPathTests:
    path_class = PaintedPath
    comp_index = 0

    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_path_elements(self, method_calls, elements, rendered):
        pth = self.path_class()

        for method, args in method_calls:
            method(pth, *args)

        assert pth._graphics_context.path_items == elements

    def test_implicit_close_insertion(self):
        pth = self.path_class()

        pth.move_to(0, 0)
        pth.line_to(1, 1)
        pth.move_to(2, 2)

        assert pth._closed is True
        assert pth._starter_move == Move(Point(2, 2))
        assert pth._graphics_context.path_items[-1] == ImplicitClose()

    def test_style_property(self):
        pth = self.path_class()
        pth.style.fill_color = "#010203"
        assert pth._graphics_context.style.fill_color == rgb8(1, 2, 3)

    def test_transform_property(self):
        pth = self.path_class()

        tf = Transform.translation(5, 10)
        pth.transform = tf

        assert pth._graphics_context.transform == tf

    def test_transform_group(self):
        pth = self.path_class()
        tf = Transform.translation(1, 2)
        with pth.transform_group(Transform.translation(1, 2)):
            assert pth._root_graphics_context != pth._graphics_context
            assert pth._graphics_context.transform == tf

    def test_auto_close(self):
        pth = self.path_class()
        pth.auto_close = True
        assert pth._root_graphics_context.style.auto_close is True

    def test_paint_rule(self):
        pth = self.path_class()
        pth.paint_rule = "auto"
        assert pth._root_graphics_context.style.paint_rule is PathPaintRule.AUTO

    @pytest.mark.parametrize("rendered", parameters.clipping_path_result)
    def test_clipping_path(self, rendered):
        pth = self.path_class()
        clp = ClippingPath()

        clp.move_to(1, 1).horizontal_line_to(9).vertical_line_to(9).horizontal_line_to(
            1
        ).close()

        pth.clipping_path = clp

        pth.move_to(0, 0)
        pth.line_to(10, 0)
        pth.line_to(5, 10)
        pth.close()

        assert pth._root_graphics_context.clipping_path == clp

        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        point = Point(0, 0)
        rend, _, __ = pth.render(resource_catalog, style, Move(point), point)
        assert rend == rendered[self.comp_index]

    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_render(self, method_calls, elements, rendered):
        # parameterized this way, this test has a lot of overlap with
        # TestPathElements.test_render, so if one breaks probably the other will. Maybe
        # it's good enough to just check a single render case instead.
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        pth = self.path_class()

        for method, args in method_calls:
            method(pth, *args)

        point = Point(0, 0)
        rend, _, __ = pth.render(resource_catalog, style, Move(point), point)
        assert rend == rendered[self.comp_index]

    def test_copy(self):
        # this is a pretty clunky way to test this, but it does make sure that copying
        # works correctly through rendering.
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        pth = self.path_class()
        pth.line_to(1, 1)

        pth2 = copy.deepcopy(pth)

        rend1, _, __ = pth.render(resource_catalog, style, start, point)
        rend2, _, __ = pth2.render(resource_catalog, style, start, point)

        pth2.line_to(2, 2)

        rend3, _, __ = pth.render(resource_catalog, style, start, point)
        rend4, _, __ = pth2.render(resource_catalog, style, start, point)

        assert rend1 == rend2 == rend3
        assert rend3 != rend4

    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_render_debug(self, method_calls, elements, rendered):
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"
        point = Point(0, 0)
        start = Move(point)
        dbg = io.StringIO()

        pth = self.path_class()

        for method, args in method_calls:
            method(pth, *args)

        rend, _, __ = pth.render(resource_catalog, style, start, point, dbg, "")
        assert rend == rendered[self.comp_index]


class TestPaintedPath(CommonPathTests):
    def test_inheriting_document_properties(self, auto_pdf_cmp):
        auto_pdf_cmp.set_line_width(0.25)
        auto_pdf_cmp.set_dash_pattern(dash=0.25, gap=0.5, phase=0.2)
        auto_pdf_cmp.set_draw_color(255, 0, 0)
        auto_pdf_cmp.set_fill_color(0, 0, 255)

        auto_pdf_cmp.compress = False

        auto_pdf_cmp.rect(1, 1, 8, 2, style="DF")

        with auto_pdf_cmp.new_path() as path:
            path.style.paint_rule = PathPaintRule.STROKE_FILL_NONZERO

            path.rectangle(1, 4, 8, 2)

        with auto_pdf_cmp.new_path() as path:
            path.style.paint_rule = PathPaintRule.STROKE_FILL_NONZERO
            path.style.stroke_width = 0.25
            path.style.stroke_dash_pattern = (0.25, 0.5)
            path.style.stroke_dash_phase = 0.2

            path.rectangle(1, 7, 8, 2)


# This class inherits all of the tests from the PaintedPath test class, just like it
# inherits all of its functionality.
class TestClippingPath(CommonPathTests):
    path_class = ClippingPath
    comp_index = 1


# these tests are all more or less redundant with the PaintedPath tests in terms of
# functionality, but having them implemented may give more information about where a
# regression occurs, if one does.
class TestGraphicsContext:
    def test_copy(self):
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        gfx = GraphicsContext()
        gfx.add_item(Move(Point(1, 2)))

        gfx2 = copy.deepcopy(gfx)

        rend1, _, __ = gfx.render(resource_catalog, style, start, point)
        rend2, _, __ = gfx2.render(resource_catalog, style, start, point)

        gfx2.add_item(Line(Point(3, 4)))

        rend3, _, __ = gfx.render(resource_catalog, style, start, point)
        rend4, _, __ = gfx2.render(resource_catalog, style, start, point)

        assert rend1 == rend2 == rend3
        assert rend3 != rend4

        assert rend1 == "q 1 2 m Q"
        assert rend4 == "q 1 2 m 3 4 l Q"

    def test_transform_property(self):
        gfx = GraphicsContext()

        tf = Transform.translation(5, 10)
        gfx.transform = tf

        assert gfx.transform == tf

    def test_clipping_path_property(self):
        gfx = GraphicsContext()
        clp = ClippingPath()

        clp.move_to(1, 1).horizontal_line_to(9).vertical_line_to(9).horizontal_line_to(
            1
        ).close()

        gfx.clipping_path = clp
        gfx.add_item(Move(Point(1, 2)))
        gfx.add_item(Line(Point(3, 4)))

        assert gfx.clipping_path == clp

        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        rend, _, __ = gfx.render(resource_catalog, style, start, point)
        assert rend == "q 1 1 m 9 1 l 9 9 l 1 9 l h W n 1 2 m 3 4 l Q"

    def test_empty_render(self):
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        tf = Transform.translation(5, 10)
        clp = ClippingPath()

        clp.move_to(1, 1).horizontal_line_to(9).vertical_line_to(9).horizontal_line_to(
            1
        ).close()

        gfx = GraphicsContext()
        gfx.clipping_path = clp
        gfx.transform = tf

        rend, _, __ = gfx.render(resource_catalog, style, start, point)
        assert rend == ""

    def test_add_item(self):
        gfx = GraphicsContext()
        gfx.add_item(Move(Point(10, 0)))

        assert gfx.path_items == [Move(Point(10, 0))]

    def test_merge(self):
        gfx1 = GraphicsContext()
        gfx1.add_item(Move(Point(10, 0)))

        gfx2 = GraphicsContext()
        gfx2.add_item(Line(Point(2, 2)))

        gfx1.merge(gfx2)

        assert gfx1.path_items == [
            Move(Point(10, 0)),
            Line(Point(2, 2)),
        ]

    def test_build_render_list(self):
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        gfx = GraphicsContext()
        gfx.add_item(Move(Point(1, 2)))
        gfx.add_item(Line(Point(3, 4)))

        rend_list1, _, __ = gfx.build_render_list(resource_catalog, style, start, point)

        assert rend_list1 == ["q", "1 2 m", "3 4 l", "Q"]

        rend_list2, _, __ = gfx.build_render_list(
            resource_catalog, style, start, point, _push_stack=False
        )

        assert rend_list2 == ["1 2 m", "3 4 l"]

    def test_render(self):
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"

        gfx = GraphicsContext()
        gfx.add_item(Move(Point(1, 2)))
        gfx.add_item(Line(Point(3, 4)))

        rend1, _, __ = gfx.render(resource_catalog, style, start, point)

        assert rend1 == "q 1 2 m 3 4 l Q"

        rend2, _, __ = gfx.render(
            resource_catalog, style, start, point, _push_stack=False
        )

        assert rend2 == "1 2 m 3 4 l"

    def test_render_debug(self):
        point = Point(0, 0)
        start = Move(point)
        resource_catalog = ResourceCatalog()
        style = GraphicsStyle()
        style.paint_rule = "auto"
        dbg = io.StringIO()

        gfx = GraphicsContext()
        gfx.add_item(Move(Point(1, 2)))
        gfx.add_item(Line(Point(3, 4)))

        rend1, _, __ = gfx.render_debug(resource_catalog, style, start, point, dbg, "")

        assert rend1 == "q 1 2 m 3 4 l Q"

        rend2, _, __ = gfx.render_debug(
            resource_catalog, style, start, point, dbg, "", _push_stack=False
        )

        assert rend2 == "1 2 m 3 4 l"


def test_check_page():
    pdf = FPDF(unit="pt")

    with pytest.raises(FPDFException) as no_page_err:
        with pdf.new_path() as _:
            pass

    expected_error_msg = "No page open, you need to call add_page() first"
    assert expected_error_msg == str(no_page_err.value)


def test_blending_images(tmp_path):
    pdf = FPDF(format=(112, 1112))
    pdf.set_margin(0)
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    for i, blend_mode in enumerate(BlendMode):
        pdf.image(HERE / "../image/png_test_suite/f04n2c08.png", y=70 * i, h=64)
        with pdf.local_context(blend_mode=blend_mode):
            pdf.image(HERE / "../image/png_test_suite/pp0n6a08.png", y=70 * i, h=64)
        pdf.text(x=0, y=70 * i + 10, text=str(blend_mode))
    assert_pdf_equal(pdf, HERE / "generated_pdf/blending_images.pdf", tmp_path)


def test_invalid_blend_mode():
    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError):
        with pdf.local_context(blend_mode="INVALID_VALUE"):
            pass
