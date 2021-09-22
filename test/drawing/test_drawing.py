# pylint: disable=redefined-outer-name, no-self-use, protected-access

from decimal import Decimal
from pathlib import Path
import re

import fpdf
from test.conftest import assert_pdf_equal

import pytest


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


@pytest.fixture(
    params=[
        ("auto_close", True),
        ("intersection_rule", "evenodd"),
        ("fill_color", None),
        ("fill_color", "#00F"),
        ("fill_color", "#00FC"),
        ("fill_color", "#00FF00"),
        ("fill_color", "#00FF007F"),
        ("fill_opacity", None),
        ("fill_opacity", 0.5),
        ("stroke_color", None),
        ("stroke_color", "#00F"),
        ("stroke_color", "#00FC"),
        ("stroke_color", "#00FF00"),
        ("stroke_color", "#00FF007F"),
        ("stroke_opacity", None),
        ("stroke_opacity", 0.5),
        ("stroke_width", None),
        ("stroke_width", 0),
        ("stroke_width", 2),
        ("stroke_join_style", "miter"),
        ("stroke_join_style", "bevel"),
        ("stroke_cap_style", "butt"),
        ("stroke_cap_style", "square"),
        ("stroke_dash_pattern", [0.5, 0.5]),
        ("stroke_dash_pattern", [1, 2, 3, 1]),
    ],
    ids=lambda val: f"{val[0]}={val[1]}",
)
def dummy_styles(request):
    return request.param


@pytest.fixture(
    params=[
        "normal",
        "multiply",
        "screen",
        "overlay",
        "darken",
        "lighten",
        "color_dodge",
        "color_burn",
        "hard_light",
        "soft_light",
        "difference",
        "exclusion",
        "hue",
        "saturation",
        "color",
        "luminosity",
    ],
    ids=lambda val: f"blend_mode={val}",
)
def blend_mode(request, open_path_drawing):
    open_path_drawing.style.fill_color = fpdf.drawing.rgb8(100, 120, 200)
    open_path_drawing.style.stroke_color = fpdf.drawing.rgb8(200, 120, 100)
    open_path_drawing.style.fill_opacity = 0.8
    open_path_drawing.style.stroke_opacity = 0.8

    return open_path_drawing, request.param


@pytest.fixture(
    params=[
        ("auto_close", 2, ValueError),
        ("paint_rule", 123, TypeError),
        ("paint_rule", "asdasd", ValueError),
        ("intersection_rule", 123, TypeError),
        ("intersection_rule", "asdasd", ValueError),
        ("fill_color", "123", ValueError),
        ("fill_color", 2, TypeError),
        ("fill_opacity", "123123", TypeError),
        ("fill_opacity", 2, ValueError),
    ],
    ids=lambda val: f"{val[0]}={val[1]}",
)
def invalid_styles(request):
    return request.param


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

    @pytest.fixture(
        params=[
            (100, "100"),
            (Decimal("1.1"), "1.1"),
            (Decimal("0.000008"), "0"),
            (1.05, "1.05"),
            (10.00001, "10"),
            (-1.12345, "-1.1235"),
            (-0.00004, "-0"),
        ],
        ids=lambda val: f"number_{val}",
    )
    def numbers(self, request):
        return request.param

    def test_hex_string_parser(self, hex_string):
        value, result = hex_string
        if isinstance(result, type) and issubclass(result, Exception):
            with pytest.raises(result):
                fpdf.drawing.color_from_hex_string(value)
        else:
            assert fpdf.drawing.color_from_hex_string(value) == result

    def test_number_to_str(self, numbers):
        assert fpdf.drawing.number_to_str(numbers[0]) == numbers[1]

    def test_range_check(self):
        ...


class TestStyles:
    def test_individual_attribute(self, auto_pdf, open_path_drawing, dummy_styles):
        sname, value = dummy_styles
        setattr(open_path_drawing.style, sname, value)

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

    def test_blend_modes(self, auto_pdf, blend_mode):
        open_path_drawing, blend_mode = blend_mode

        open_path_drawing.style.blend_mode = blend_mode

        auto_pdf.draw_path(open_path_drawing)

    def test_dictionary_generation(self, dummy_styles):
        _ = dummy_styles

    def test_bad_style_parameters(self, invalid_styles):
        attr, value, exc = invalid_styles

        style = fpdf.drawing.GraphicsStyle()
        with pytest.raises(exc):
            setattr(style, attr, value)

    def test_merge(self):
        ...

    def test_style_lookup(self):
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
