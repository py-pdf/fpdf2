# pylint: disable=redefined-outer-name, no-self-use, protected-access, unused-argument

import copy
import io
import math
from pathlib import Path
import re

import fpdf
from test.conftest import assert_pdf_equal

import pytest

from . import parameters


HERE = Path(__file__).resolve().parent
bad_path_chars = re.compile(r"[\[\]=#, ]")


@pytest.fixture(scope="function")
def auto_pdf(request, tmp_path):
    pdf = fpdf.FPDF(unit="mm", format=(10, 10))
    pdf.add_page()

    yield pdf

    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / f"{bad_path_chars.sub('_', request.node.name)}.pdf",
        tmp_path,
    )


@pytest.fixture
def open_path_drawing():
    path = fpdf.drawing.PaintedPath()
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
    open_path_drawing.style.fill_color = fpdf.drawing.rgb8(100, 120, 200)
    open_path_drawing.style.stroke_color = fpdf.drawing.rgb8(200, 120, 100)
    open_path_drawing.style.fill_opacity = 0.8
    open_path_drawing.style.stroke_opacity = 0.8

    return open_path_drawing


class TestUtilities:
    def test_range_check(self):
        with pytest.raises(ValueError):
            fpdf.drawing._check_range(-1, minimum=0.0, maximum=0.0)

        fpdf.drawing._check_range(0, minimum=0.0, maximum=1.0)
        fpdf.drawing._check_range(1, minimum=0.0, maximum=1.0)

    @pytest.mark.parametrize("number, converted", parameters.numbers)
    def test_number_to_str(self, number, converted):
        assert fpdf.drawing.number_to_str(number) == converted

    @pytest.mark.parametrize("primitive, result", parameters.pdf_primitives)
    def test_render_primitive(self, primitive, result):
        assert fpdf.drawing.render_pdf_primitive(primitive) == result

    # TODO: add check for bad primitives: class without pdf_repr, dict with non-Name
    # keys. Check for proper escaping of Name and string edge cases


class TestGraphicsStateDictRegistry:
    @pytest.fixture
    def new_style_registry(self):
        return fpdf.drawing.GraphicsStateDictRegistry()

    def test_empty_style(self, new_style_registry):
        style = fpdf.drawing.GraphicsStyle()

        result = new_style_registry.register_style(style)

        assert result is None

    def test_adding_styles(self, new_style_registry):
        first = fpdf.drawing.GraphicsStyle()
        second = fpdf.drawing.GraphicsStyle()

        first.stroke_width = 1
        second.stroke_width = 2

        first_name = new_style_registry.register_style(first)
        second_name = new_style_registry.register_style(second)

        assert isinstance(first_name, fpdf.drawing.Name)
        assert isinstance(second_name, fpdf.drawing.Name)
        assert first_name != second_name
        # I don't think it's necessary to check that first_name is actually e.g. "GS1", since
        # the naming pattern is an implementation detail that can change without
        # affecting anything.

    def test_style_deduplication(self, new_style_registry):
        first = fpdf.drawing.GraphicsStyle()
        second = fpdf.drawing.GraphicsStyle()

        first.stroke_width = 1
        second.stroke_width = 1

        first_name = new_style_registry.register_style(first)
        second_name = new_style_registry.register_style(second)

        assert isinstance(first_name, fpdf.drawing.Name)
        assert isinstance(second_name, fpdf.drawing.Name)
        assert first_name == second_name


class TestColors:
    def test_device_rgb(self):
        rgb = fpdf.drawing.DeviceRGB(r=1, g=0.5, b=0.25)
        rgba = fpdf.drawing.DeviceRGB(r=1, g=0.5, b=0.25, a=0.75)

        assert rgb.colors == (1, 0.5, 0.25)
        assert rgba.colors == (1, 0.5, 0.25)

        with pytest.raises(ValueError):
            fpdf.drawing.DeviceRGB(r=2, g=1, b=0)

    def test_device_gray(self):
        gray = fpdf.drawing.DeviceGray(g=0.5)
        gray_a = fpdf.drawing.DeviceGray(g=0.5, a=0.75)

        assert gray.colors == (0.5,)
        assert gray_a.colors == (0.5,)

        with pytest.raises(ValueError):
            fpdf.drawing.DeviceGray(g=2)

    def test_device_cmyk(self):
        cmyk = fpdf.drawing.DeviceCMYK(c=1, m=1, y=1, k=0)
        cmyk_a = fpdf.drawing.DeviceCMYK(c=1, m=1, y=1, k=0, a=0.5)

        assert cmyk.colors == (1, 1, 1, 0)
        assert cmyk_a.colors == (1, 1, 1, 0)

        with pytest.raises(ValueError):
            fpdf.drawing.DeviceCMYK(c=2, m=1, y=1, k=0)

    def test_rgb8(self):
        rgb = fpdf.drawing.rgb8(255, 254, 253)
        rgba = fpdf.drawing.rgb8(r=255, g=254, b=253, a=252)

        assert rgb == fpdf.drawing.DeviceRGB(r=1.0, g=254 / 255, b=253 / 255)
        assert rgba == fpdf.drawing.DeviceRGB(
            r=1.0, g=254 / 255, b=253 / 255, a=252 / 255
        )

    def test_gray8(self):
        gray = fpdf.drawing.gray8(255)
        gray_a = fpdf.drawing.gray8(g=255, a=254)

        assert gray == fpdf.drawing.DeviceGray(g=1.0)
        assert gray_a == fpdf.drawing.DeviceGray(g=1.0, a=254 / 255)

    def test_cmyk8(self):
        cmyk = fpdf.drawing.cmyk8(255, 254, 253, 252)
        cmyk_a = fpdf.drawing.cmyk8(c=255, m=254, y=253, k=252, a=251)

        assert cmyk == fpdf.drawing.DeviceCMYK(
            c=1.0, m=254 / 255, y=253 / 255, k=252 / 255
        )
        assert cmyk_a == fpdf.drawing.DeviceCMYK(
            c=1.0, m=254 / 255, y=253 / 255, k=252 / 255, a=251 / 255
        )

    @pytest.mark.parametrize("hex_string, result", parameters.hex_colors)
    def test_hex_string_parser(self, hex_string, result):
        if isinstance(result, type) and issubclass(result, Exception):
            with pytest.raises(result):
                fpdf.drawing.color_from_hex_string(hex_string)
        else:
            assert fpdf.drawing.color_from_hex_string(hex_string) == result


class TestPoint:
    def test_render(self):
        pt = fpdf.drawing.Point(1, 1)

        assert pt.render() == "1 1"

    def test_dot(self):
        pt1 = fpdf.drawing.Point(1, 2)
        pt2 = fpdf.drawing.Point(3, 4)

        assert pt1.dot(pt2) == 11
        assert pt2.dot(pt1) == 11

        with pytest.raises(TypeError):
            pt1.dot(1)

    def test_angle(self):
        pt1 = fpdf.drawing.Point(1, 0)
        pt2 = fpdf.drawing.Point(0, 1)

        assert pt1.angle(pt2) == pytest.approx(math.pi / 2)
        assert pt2.angle(pt1) == pytest.approx(-(math.pi / 2))

        with pytest.raises(TypeError):
            pt1.angle(1)

    def test_magnitude(self):
        pt1 = fpdf.drawing.Point(2, 0)

        assert pt1.mag() == 2.0

    def test_add(self):
        pt1 = fpdf.drawing.Point(1, 0)
        pt2 = fpdf.drawing.Point(0, 1)

        assert pt1 + pt2 == fpdf.drawing.Point(1, 1)
        assert pt2 + pt1 == fpdf.drawing.Point(1, 1)

        with pytest.raises(TypeError):
            _ = pt1 + 2

    def test_sub(self):
        pt1 = fpdf.drawing.Point(1, 0)
        pt2 = fpdf.drawing.Point(0, 1)

        assert pt1 - pt2 == fpdf.drawing.Point(1, -1)
        assert pt2 - pt1 == fpdf.drawing.Point(-1, 1)

        with pytest.raises(TypeError):
            _ = pt1 - 2

    def test_neg(self):
        pt = fpdf.drawing.Point(1, 2)

        assert -pt == fpdf.drawing.Point(-1, -2)

    def test_mul(self):
        pt = fpdf.drawing.Point(1, 2)

        assert pt * 2 == fpdf.drawing.Point(2, 4)
        assert 2 * pt == fpdf.drawing.Point(2, 4)

        with pytest.raises(TypeError):
            _ = pt * pt

    def test_div(self):
        pt = fpdf.drawing.Point(1, 2)

        assert (pt / 2) == fpdf.drawing.Point(0.5, 1.0)
        assert (pt // 2) == fpdf.drawing.Point(0, 1)

        with pytest.raises(TypeError):
            _ = 2 / pt

        with pytest.raises(TypeError):
            _ = 2 // pt

        with pytest.raises(TypeError):
            _ = pt / pt

        with pytest.raises(TypeError):
            _ = pt // pt

    def test_matmul(self):
        pt = fpdf.drawing.Point(2, 4)
        tf = fpdf.drawing.Transform.translation(2, 2)

        assert pt @ tf == fpdf.drawing.Point(4, 6)

        with pytest.raises(TypeError):
            _ = tf @ pt

        with pytest.raises(TypeError):
            _ = pt @ pt

    def test_str(self):
        pt = fpdf.drawing.Point(2, 4)

        assert str(pt) == "(x=2, y=4)"


class TestTransform:
    # TODO: figure out a better way to test these constructors
    @pytest.mark.parametrize("tf, pt, result", parameters.transforms)
    def test_constructors(self, tf, pt, result):
        # use of pytest.approx here works because fpdf.drawing.Point is a NamedTuple
        # (approx supports tuples) and wouldn't work if it were a normal object
        assert pt @ tf == pytest.approx(result)

    def test_chaining(self):
        tf = (
            fpdf.drawing.Transform.identity()
            .translate(1, 1)
            .scale(2, 1)
            .rotate(0.3)
            .shear(0, 0.5)
        )
        assert tf == pytest.approx(
            fpdf.drawing.Transform(
                a=1.910672978251212,
                b=1.546376902448285,
                c=-0.29552020666133955,
                d=0.8075763857949362,
                e=1.6151527715898724,
                f=2.353953288243221,
            )
        )

    def test_about(self):
        tf = fpdf.drawing.Transform.scaling(2).about(10, 10)

        assert tf == fpdf.drawing.Transform(a=2, b=0, c=0, d=2, e=-10, f=-10)
        assert tf == fpdf.drawing.Transform.translation(-10, -10).scale(2).translate(
            10, 10
        )

    def test_mul(self):
        tf = fpdf.drawing.Transform(1, 2, 3, 4, 5, 6)

        assert tf * 6 == fpdf.drawing.Transform(6, 12, 18, 24, 30, 36)
        assert 6 * tf == fpdf.drawing.Transform(6, 12, 18, 24, 30, 36)

        with pytest.raises(TypeError):
            _ = tf * "abc"

    def test_matmul(self):
        tf1 = fpdf.drawing.Transform(1, 2, 3, 4, 5, 6)
        tf2 = fpdf.drawing.Transform(6, 5, 4, 3, 2, 1)

        assert tf1 @ tf2 == fpdf.drawing.Transform(a=14, b=11, c=34, d=27, e=56, f=44)
        assert tf2 @ tf1 == fpdf.drawing.Transform(a=21, b=32, c=13, d=20, e=10, f=14)

        with pytest.raises(TypeError):
            _ = tf1 @ 123

    def test_render(self):
        tf = fpdf.drawing.Transform(1, 2, 3, 4, 5, 6)

        assert (
            tf.render(fpdf.drawing.Move(fpdf.drawing.Point(0, 0)))[0]
            == "1 2 3 4 5 6 cm"
        )

    def test_str(self):
        # don't actually assert the output looks like something in particular, just make
        # sure it doesn't raise, I guess.
        str(fpdf.drawing.Transform(1, 2, 3, 4, 5, 6))


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
    def test_individual_attribute(self, auto_pdf, open_path_drawing, style_name, value):
        setattr(open_path_drawing.style, style_name, value)

        auto_pdf.draw_path(open_path_drawing)

    def test_stroke_miter_limit(self, auto_pdf, open_path_drawing):
        open_path_drawing.style.stroke_join_style = "miter"
        open_path_drawing.style.stroke_miter_limit = 1.4

        auto_pdf.draw_path(open_path_drawing)

    def test_stroke_dash_phase(self, auto_pdf, open_path_drawing):
        open_path_drawing.style.stroke_dash_pattern = [0.5, 0.5]
        open_path_drawing.style.stroke_dash_phase = 0.5

        auto_pdf.draw_path(open_path_drawing)

    def test_illegal_stroke_dash_phase(self, open_path_drawing):
        open_path_drawing.style.stroke_dash_pattern = fpdf.drawing.GraphicsStyle.INHERIT

        with pytest.raises(ValueError):
            open_path_drawing.style.stroke_dash_phase = 0.5

    @pytest.mark.parametrize(
        "blend_mode", parameters.blend_modes, ids=lambda param: f"blend mode {param}"
    )
    def test_blend_modes(
        self, auto_pdf, open_path_drawing, prepared_blend_path, blend_mode
    ):
        prepared_blend_path.style.blend_mode = blend_mode

        auto_pdf.draw_path(open_path_drawing)

    def test_dictionary_generation(self):
        style = fpdf.drawing.GraphicsStyle()

        style.fill_opacity = 0.5
        style.stroke_opacity = 0.75
        style.blend_mode = "lighten"
        style.stroke_width = 2
        style.stroke_join_style = "round"
        style.stroke_cap_style = "butt"

        assert (
            style.to_pdf_dict()
            == "<< /Type /ExtGState\n/ca 0.5\n/BM /Lighten\n/CA 0.75\n/LW 2\n/LC 0\n/LJ 1 >>"
        )

    @pytest.mark.parametrize("style_name, value, exception", parameters.invalid_styles)
    def test_bad_style_parameters(self, style_name, value, exception):
        style = fpdf.drawing.GraphicsStyle()
        with pytest.raises(exception):
            setattr(style, style_name, value)

    def test_merge(self):
        style = fpdf.drawing.GraphicsStyle()

        style.fill_opacity = 0.5
        style.stroke_opacity = 0.75
        style.blend_mode = "lighten"
        style.stroke_width = 2
        style.stroke_join_style = "round"
        style.stroke_cap_style = "butt"

        override = fpdf.drawing.GraphicsStyle()

        override.fill_opacity = 0.25
        override.stroke_opacity = 0.1
        override.blend_mode = "hue"

        merged = fpdf.drawing.GraphicsStyle.merge(style, override)

        assert merged.fill_opacity == 0.25
        assert merged.stroke_opacity == 0.1
        assert merged.blend_mode == fpdf.drawing.BlendMode.HUE.value
        assert merged.stroke_width == 2
        assert merged.stroke_join_style == fpdf.drawing.StrokeJoinStyle.ROUND.value
        assert merged.stroke_cap_style == fpdf.drawing.StrokeCapStyle.BUTT.value

    def test_paint_rule_resolution(self):
        style = fpdf.drawing.GraphicsStyle()

        style.paint_rule = "auto"

        assert (
            style.resolve_paint_rule() is fpdf.drawing.PathPaintRule.STROKE_FILL_NONZERO
        )

        style.stroke_width = 2
        style.stroke_color = "#000"
        style.fill_color = None
        assert style.resolve_paint_rule() is fpdf.drawing.PathPaintRule.STROKE

        style.fill_color = "#123"
        assert (
            style.resolve_paint_rule() is fpdf.drawing.PathPaintRule.STROKE_FILL_NONZERO
        )

        style.intersection_rule = fpdf.drawing.IntersectionRule.EVENODD
        assert (
            style.resolve_paint_rule() is fpdf.drawing.PathPaintRule.STROKE_FILL_EVENODD
        )

    def test_copy(self):
        style = fpdf.drawing.GraphicsStyle()

        style.fill_opacity = 0.5

        copied = copy.deepcopy(style)

        copied.fill_opacity = 1.0

        assert style is not copied
        assert style.fill_opacity != copied.fill_opacity


class TestPathElements:
    @pytest.mark.parametrize(
        "start, element, expected, end_point, end_class", parameters.path_elements
    )
    def test_render(self, start, element, expected, end_point, end_class):
        style = fpdf.drawing.GraphicsStyle()
        style.auto_close = False
        rendered, last_item = element.render({}, style, start)

        assert rendered == expected
        assert isinstance(last_item, end_class)
        assert last_item.end_point == pytest.approx(end_point)

    @pytest.mark.parametrize(
        "start, element, expected, end_point, end_class", parameters.path_elements
    )
    def test_render_debug(self, start, element, expected, end_point, end_class):
        dbg = io.StringIO()
        style = fpdf.drawing.GraphicsStyle()
        style.auto_close = False
        rendered, last_item = element.render_debug({}, style, start, dbg, "")

        assert rendered == expected
        assert isinstance(last_item, end_class)
        assert last_item.end_point == pytest.approx(end_point)


class TestDrawingContext:
    def test_add_item(self):
        ctx = fpdf.drawing.DrawingContext()

        ctx.add_item(fpdf.drawing.GraphicsContext())

        with pytest.raises(TypeError):
            ctx.add_item(fpdf.drawing.Move(fpdf.drawing.Point(1, 2)))

    def test_empty_render(self):
        ctx = fpdf.drawing.DrawingContext()
        ctx.add_item(fpdf.drawing.GraphicsContext())

        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))

        result = ctx.render(gsdr, start, 1, 10)

        assert result == ""

    def test_render(self):
        ctx = fpdf.drawing.DrawingContext()
        ctx.add_item(fpdf.drawing.PaintedPath().line_to(10, 10))

        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))

        result = ctx.render(gsdr, start, 1, 10)

        assert result == "q 1 0 0 -1 0 10 cm q 0 0 m 10 10 l h B Q Q"

    def test_empty_render_debug(self):
        ctx = fpdf.drawing.DrawingContext()
        ctx.add_item(fpdf.drawing.GraphicsContext())

        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))
        dbg = io.StringIO()

        result = ctx.render_debug(gsdr, start, 1, 10, dbg)

        assert result == ""

    def test_render_debug(self):
        ctx = fpdf.drawing.DrawingContext()
        ctx.add_item(fpdf.drawing.PaintedPath().line_to(10, 10))

        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))
        dbg = io.StringIO()

        result = ctx.render_debug(gsdr, start, 1, 10, dbg)

        assert result == "q 1 0 0 -1 0 10 cm q 0 0 m 10 10 l h B Q Q"


class TestPaintedPath:
    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_path_elements(self, method_calls, elements, rendered):
        pth = fpdf.drawing.PaintedPath()

        for method, args in method_calls:
            method(pth, *args)

        assert pth._graphics_context.path_items == elements

    def test_implicit_close_insertion(self):
        pth = fpdf.drawing.PaintedPath()

        pth.move_to(0, 0)
        pth.line_to(1, 1)
        pth.move_to(2, 2)

        assert pth._closed is True
        assert pth._starter_move == fpdf.drawing.Move(fpdf.drawing.Point(2, 2))
        assert pth._graphics_context.path_items[-1] == fpdf.drawing.ImplicitClose()

    def test_style(self):
        pth = fpdf.drawing.PaintedPath()
        pth.style.fill_color = "#010203"
        assert pth._graphics_context.style.fill_color == fpdf.drawing.rgb8(1, 2, 3)

    def test_transform(self):
        pth = fpdf.drawing.PaintedPath()

        tf = fpdf.drawing.Transform.translation(5, 10)
        pth.transform = tf

        assert pth._graphics_context.transform == tf

    def test_transform_group(self):
        pth = fpdf.drawing.PaintedPath()
        tf = fpdf.drawing.Transform.translation(1, 2)
        with pth.transform_group(fpdf.drawing.Transform.translation(1, 2)):
            assert pth._root_graphics_context != pth._graphics_context
            assert pth._graphics_context.transform == tf

    def test_auto_close(self):
        pth = fpdf.drawing.PaintedPath()
        pth.auto_close = True
        assert pth._root_graphics_context.style.auto_close is True

    def test_paint_rule(self):
        pth = fpdf.drawing.PaintedPath()
        pth.paint_rule = "auto"
        assert (
            pth._root_graphics_context.style.paint_rule
            is fpdf.drawing.PathPaintRule.AUTO
        )

    def test_clipping_path(self):
        pth = fpdf.drawing.PaintedPath()
        clp = fpdf.drawing.ClippingPath()

        pth.clipping_path = clp

        assert pth._root_graphics_context.clipping_path == clp

    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_render(self, method_calls, elements, rendered):
        # parameterized this way, this test has a lot of overlap with
        # TestPathElements.test_render, so if one breaks probably the other will. Maybe
        # it's good enough to just check a single render case instead.
        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        style = fpdf.drawing.GraphicsStyle()
        style.paint_rule = "auto"

        pth = fpdf.drawing.PaintedPath()

        for method, args in method_calls:
            method(pth, *args)

        rend, _ = pth.render(gsdr, style, fpdf.drawing.Move(fpdf.drawing.Point(0, 0)))
        assert rend == rendered

    def test_copy(self):
        # this is a pretty clunky way to test this, but it does make sure that copying
        # works correctly through rendering.
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))
        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        style = fpdf.drawing.GraphicsStyle()
        style.paint_rule = "auto"

        pth = fpdf.drawing.PaintedPath()
        pth.line_to(1, 1)

        pth2 = copy.deepcopy(pth)

        rend1, _ = pth.render(gsdr, style, start)
        rend2, _ = pth2.render(gsdr, style, start)

        pth2.line_to(2, 2)

        rend3, _ = pth.render(gsdr, style, start)
        rend4, _ = pth2.render(gsdr, style, start)

        assert rend1 == rend2 == rend3
        assert rend3 != rend4

    @pytest.mark.parametrize(
        "method_calls, elements, rendered", parameters.painted_path_elements
    )
    def test_render_debug(self, method_calls, elements, rendered):
        gsdr = fpdf.drawing.GraphicsStateDictRegistry()
        style = fpdf.drawing.GraphicsStyle()
        style.paint_rule = "auto"
        start = fpdf.drawing.Move(fpdf.drawing.Point(0, 0))
        dbg = io.StringIO()

        pth = fpdf.drawing.PaintedPath()

        for method, args in method_calls:
            method(pth, *args)

        rend, _ = pth.render(gsdr, style, start, dbg, "")
        assert rend == rendered


class TestClippingPath:
    ...


class TestGraphicsContext:
    ...


def test_check_page():
    pdf = fpdf.FPDF(unit="pt")

    with pytest.raises(fpdf.FPDFException) as no_page_err:
        with pdf.new_path() as _:
            pass

    expected_error_msg = "No page open, you need to call add_page() first"
    assert expected_error_msg == str(no_page_err.value)
