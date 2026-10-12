from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from io import BytesIO

import pytest
from pypdf import PdfReader
from pypdf.generic import read_object

from fpdf import FPDF

from fpdf.syntax import (
    DestinationXYZ,
    Name,
    PDFArray,
    PDFDate,
    PDFObject,
    PDFString,
    create_dictionary_string,
)


class DummyObj(PDFObject):
    def __init__(self, obj_id: int):
        super().__init__()
        self.id = obj_id


@pytest.mark.parametrize("number", [1e-7, -1e-7, 1.25e20, 1.234567890123456e-20])
@pytest.mark.parametrize("mixed", [False, True])
def test_pdf_array_float_exponents_are_written_as_decimals(number, mixed):
    elements = [number, None] if mixed else [number]
    parsed = read_object(BytesIO(PDFArray(elements).serialize().encode()), None)
    assert len(parsed) == len(elements)
    assert float(parsed[0]) == number


@pytest.mark.parametrize("number", [1e-7, -1e-7, 1.25e20, 1.234567890123456e-20])
def test_pdf_dictionary_float_exponents_are_written_as_decimals(number):
    serialized = create_dictionary_string({"/Value": number})
    parsed = read_object(BytesIO(serialized.encode()), None)
    assert float(parsed["/Value"]) == number


def test_display_mode_with_small_numeric_zoom():
    zoom = 0.00001
    pdf = FPDF()
    pdf.add_page()
    pdf.set_display_mode(zoom)
    reader = PdfReader(BytesIO(pdf.output()), strict=True)
    assert float(reader.trailer["/Root"]["/OpenAction"][-1]) == zoom / 100


@pytest.mark.parametrize("year", [1, 12, 123, 999, 1000, 2026])
@pytest.mark.parametrize(
    "zone,with_tz,suffix",
    [
        (None, False, ""),
        (timezone.utc, True, "Z"),
        (timezone(timedelta(hours=-3, minutes=-30)), True, "-03'30'"),
    ],
)
def test_pdf_date_four_digit_year(year, zone, with_tz, suffix):
    value = datetime(year, 1, 2, 3, 4, 5, tzinfo=zone)
    assert PDFDate(value, with_tz=with_tz).serialize() == (
        f"(D:{year:04d}0102030405{suffix})"
    )


@pytest.mark.parametrize(
    "elements,expected",
    [
        ([], "[]"),
        (["a", "b"], "[a b]"),
        ([1, 2, 3], "[1 2 3]"),
        ([1.5, 2.0], "[1.5 2]"),
        ([True], "[true]"),
        ([False], "[false]"),
        ([True, False], "[true false]"),
        ([False, True, False], "[false true false]"),
        ([1, True], "[1\ntrue]"),
        ([False, 0], "[false\n0]"),
        ([DummyObj(1), True], "[1 0 R\ntrue]"),
        ([None], "[null]"),
        ([None, None], "[null null]"),
        ([1, None], "[1\nnull]"),
        ([None, True], "[null\ntrue]"),
        ([DummyObj(1), None], "[1 0 R\nnull]"),
    ],
)
def test_pdf_array_serialize_booleans_and_numbers(elements, expected):
    array = PDFArray(elements)
    assert array.serialize() == expected


@pytest.mark.parametrize(
    "elements,expected",
    [
        ([PDFString("hello")], "[(hello)]"),
        ([PDFString("Hello (world)")], r"[(Hello \(world\))]"),
        ([PDFString("é")], "[<feff00e9>]"),
        ([Name("Example Name")], "[/Example#20Name]"),
        ([PDFString("hello"), Name("my name")], "[(hello)\n/my#20name]"),
        (["/Literal", PDFString("hi")], "[/Literal\n(hi)]"),
    ],
)
def test_pdf_array_serializable_strings(elements, expected):
    assert PDFArray(elements).serialize() == expected


def test_pdf_array_serializable_strings_encryption():
    security_handler = Mock()
    security_handler.encrypt_string.return_value = "(ciphertext)"
    value = PDFString("secret", encrypt=True)
    assert (
        PDFArray([value]).serialize(_security_handler=security_handler, _obj_id=3)
        == "[(ciphertext)]"
    )
    security_handler.encrypt_string.assert_called_once_with(value, 3)


@pytest.mark.parametrize(
    "dict_input,field_join,key_value_join,expected",
    [
        (
            {"/Marked": True},
            "\n",
            " ",
            "<</Marked true>>",
        ),
        (
            {"/Flag": False},
            "\n",
            " ",
            "<</Flag false>>",
        ),
        (
            {"/A": True, "/B": False, "/Count": 42},
            " ",
            " ",
            "<</A true /B false /Count 42>>",
        ),
        (
            {"/Active": True, "/Empty": None},
            "\n",
            " ",
            "<</Active true>>",
        ),
    ],
)
def test_create_dictionary_string_booleans(
    dict_input, field_join, key_value_join, expected
):
    result = create_dictionary_string(
        dict_input,
        open_dict="<<",
        close_dict=">>",
        field_join=field_join,
        key_value_join=key_value_join,
        has_empty_fields=True,
    )
    assert result == expected


@pytest.mark.parametrize(
    "dict_input,field_join,key_value_join,has_empty_fields,expected",
    [
        (
            {"/Key": None},
            "\n",
            " ",
            False,
            "<</Key null>>",
        ),
        (
            {"/A": None, "/B": True, "/C": False, "/Count": 0},
            " ",
            " ",
            False,
            "<</A null /B true /C false /Count 0>>",
        ),
        (
            {"/Empty": None},
            "",
            " ",
            False,
            "<</Empty null>>",
        ),
    ],
)
def test_create_dictionary_string_null(
    dict_input, field_join, key_value_join, has_empty_fields, expected
):
    result = create_dictionary_string(
        dict_input,
        open_dict="<<",
        close_dict=">>",
        field_join=field_join,
        key_value_join=key_value_join,
        has_empty_fields=has_empty_fields,
    )
    assert result == expected


@pytest.mark.parametrize(
    "elements,expected",
    [
        ([100.0, -0.0, 1.123456789012345], "[100 -0 1.123456789012345]"),
        ([1.0, True, None, 1.123456789012345], "[1\ntrue\nnull\n1.123456789012345]"),
        ([1e20, 1e-20], "[100000000000000000000 0.00000000000000000001]"),
        (["1.00", "(2.00)"], "[1.00 (2.00)]"),
    ],
)
def test_pdf_array_trailing_zeros_preserve_precision(elements, expected):
    assert PDFArray(elements).serialize() == expected


def test_dictionary_trailing_zeros_preserve_precision():
    assert (
        create_dictionary_string({"/A": 100.0, "/B": 1.123456789012345, "/C": "(2.00)"})
        == "<</A 100\n/B 1.123456789012345\n/C (2.00)>>"
    )


def test_destination_trailing_zeros_preserve_rounding():
    dest = DestinationXYZ(page=1, top=123.456, left=10.0, zoom=1.0)
    dest.page_ref = "3 0 R"
    assert dest.serialize() == "[3 0 R /XYZ 10 123.46 1]"
