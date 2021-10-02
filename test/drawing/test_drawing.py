# pylint: disable=redefined-outer-name, no-self-use, protected-access

from decimal import Decimal
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
    @pytest.fixture(
        params=[
            ("#CAB", fpdf.drawing.rgb8(r=0xCC, g=0xAA, b=0xBB, a=None)),
            ("#FADE", fpdf.drawing.rgb8(r=0xFF, g=0xAA, b=0xDD, a=0xEE)),
            ("#C0FFEE", fpdf.drawing.rgb8(r=0xC0, g=0xFF, b=0xEE, a=None)),
            ("#0D06F00D", fpdf.drawing.rgb8(r=0x0D, g=0x06, b=0xF0, a=0x0D)),
            ("asd", ValueError),
            ("#12345", ValueError),
            (123, TypeError),
        ],
        ids=lambda val: f"hex_string_{val[1]}",
    )
    def hex_string(self, request):
        return request.param

    def test_hex_string_parser(self, hex_string):
        value, result = hex_string
        if isinstance(result, type) and issubclass(result, Exception):
            with pytest.raises(result):
                fpdf.drawing.color_from_hex_string(value)
        else:
            assert fpdf.drawing.color_from_hex_string(value) == result

    @pytest.mark.parametrize("number, converted", parameters.numbers)
    def test_number_to_str(self, number, converted):
        assert fpdf.drawing.number_to_str(number) == converted

    def test_range_check(self):
        ...


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


class TestPoint:
    def test_render(self):
        ...

    def test_dot(self):
        ...

    def test_angle(self):
        ...

    def test_magnitude(self):
        ...

    def test_add(self):
        ...

    def test_sub(self):
        ...

    def test_neg(self):
        ...

    def test_mul(self):
        ...  # also test rmul

    def test_matmul(self):
        ...

    def test_str(self):
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
