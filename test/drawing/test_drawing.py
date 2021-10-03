# pylint: disable=redefined-outer-name, no-self-use, protected-access

from decimal import Decimal
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
        # use of pytest.approx here works because fpdf.drawing.Point is a NamedTuple and
        # wouldn't work otherwise
        assert pt @ tf == pytest.approx(result)


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
        pass

    @pytest.mark.parametrize("style_name, value, exception", parameters.invalid_styles)
    def test_bad_style_parameters(self, style_name, value, exception):
        style = fpdf.drawing.GraphicsStyle()
        with pytest.raises(exception):
            setattr(style, style_name, value)

    def test_merge(self):
        ...

    def test_pdf_dictionary_converion(self):
        ...


# def test_path_creation(tmp_path):
#     pdf = fpdf.FPDF(unit="mm", format=(10, 10))
#     pdf.add_page()

#     with pdf.path(x=2, y=2) as path:
#         path.style.fill_color = fpdf.drawing.rgb8(r=200, g=180, b=255)
#         path.style.stroke_color = fpdf.drawing.gray8(g=50)
#         path.style.stroke_width = 0.5
#         path.style.stroke_join_style = "miter"
#         path.style.stroke_miter_limit = 2
#         path.style.auto_close = True

#         path.line_to(8, 8)
#         path.line_to(8, 2)

#         path.move_to(3.5, 6.5)
#         path.line_to(3.5, 3.5)
#         path.line_to(6.5, 3.5)
#         path.line_to(6.5, 6.5)

#     assert_pdf_equal(pdf, HERE / "drawing_basic.pdf", tmp_pat


# def test_path_transforms(tmp_path):
#     pdf = fpdf.FPDF(unit="mm", format=(10, 10))
#     pdf.add_page()

#     with pdf.path(x=2, y=2) as path:
#         path.style.stroke_color = fpdf.drawing.gray8(g=50)
#         path.style.stroke_width = 0.25
#         path.style.stroke_join_style = "miter"
#         path.style.stroke_miter_limit = 2

#         with path.transform_group(fpdf.drawing.Transform.rotation_d(15)):
#             path.move_to(0, 0)
#             path.line_to(8, 0)

#         with path.transform_group(fpdf.drawing.Transform.rotation_d(30)):
#             path.move_to(0, 0)
#             path.line_to(8, 0)

#     assert_pdf_equal(pdf, HERE / "drawing_rotation.pdf", tmp_pat


def test_check_page():
    pdf = fpdf.FPDF(unit="pt")

    with pytest.raises(fpdf.FPDFException) as no_page_err:
        with pdf.new_path() as _:
            pass

    expected_error_msg = "No page open, you need to call add_page() first"
    assert expected_error_msg == str(no_page_err.value)
