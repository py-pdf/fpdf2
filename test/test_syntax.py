import pytest

from fpdf.syntax import DestinationXYZ, PDFArray, PDFObject, create_dictionary_string


class DummyObj(PDFObject):
    def __init__(self, obj_id: int):
        super().__init__()
        self.id = obj_id


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
        ([1e20, 1e-20], "[1e+20 1e-20]"),
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
