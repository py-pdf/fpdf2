import pytest

from fpdf.syntax import PDFArray, PDFObject


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
        ([1.5, 2.0], "[1.5 2.0]"),
        ([True], "[true]"),
        ([False], "[false]"),
        ([True, False], "[true false]"),
        ([False, True, False], "[false true false]"),
        ([1, True], "[1\ntrue]"),
        ([False, 0], "[false\n0]"),
        ([DummyObj(1), True], "[1 0 R\ntrue]"),
    ],
)
def test_pdf_array_serialize_booleans_and_numbers(elements, expected):
    array = PDFArray(elements)
    assert array.serialize() == expected
