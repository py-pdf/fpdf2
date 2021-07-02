import math

from fpdf.util import convert_unit


def test_convert_unit_number_number():
    """Test converting units where both old and new are numbers"""
    converted = convert_unit(1, 72, 72 / 25.4)  # inch to mm
    assert math.isclose(converted, 25.4), "1 inch should equal 25.4 mm at 72dpi"


def test_convert_unit_number_string():
    """Test converting units where old is a number and new is a string"""
    converted = convert_unit(1, 72, "mm")  # inch to mm
    assert math.isclose(converted, 25.4), "1 inch should equal 25.4 mm at 72dpi"


def test_convert_unit_string_number():
    """Test converting units where old is a string and new is a number"""
    converted = convert_unit(1, "in", 72 / 25.4)  # inch to mm
    assert math.isclose(converted, 25.4), "1 inch should equal 25.4 mm at 72dpi"


def test_convert_unit_string_string():
    """Test converting units where both old and new are strings"""
    converted = convert_unit(1, "in", "mm")
    assert math.isclose(converted, 25.4), "1 inch should equal 25.4 mm at 72dpi"


def test_convert_unit_tuple():
    """
    Test converting a simple tuple

    Eg. The output of `get_page_format("letter", 1)`
    """
    inches = convert_unit((612, 792), "pt", "in")
    assert inches == (8.5, 11.0)


def test_convert_unit_list():
    """Test converting a simple list"""
    inches = convert_unit([612, 792], "pt", "in")
    assert inches == (8.5, 11.0)


def test_convert_unit_iterator():
    """Test converting a simple iterator"""
    inches = convert_unit(iter([612, 792]), "pt", "in")
    assert inches == (8.5, 11.0)


def test_convert_unit_list_of_points():
    """Test converting a list of points"""
    inches = convert_unit([(72, 72), (612, 792)], "pt", "in")
    assert inches == ((1, 1), (8.5, 11.0))


def test_convert_unit_crazy():
    """
    Test converting a tuple which holds a list/iterator/tuple which contains points.
    This would be creating points for multiple pdfs at once, where each page of each pdf has its own unique point grid.
    """
    to_convert = (
        [iter([8.5, 11]), [1, 1]],
        ((1, 1), (8.5, 11)),
        iter([(2, 2), (11, 8.5)]),
    )
    converted = convert_unit(to_convert, "in", "mm")
    assert converted == (
        ((215.89999999999998, 279.4), (25.399999999999995, 25.399999999999995)),
        ((25.399999999999995, 25.399999999999995), (215.89999999999998, 279.4)),
        ((50.79999999999999, 50.79999999999999), (279.4, 215.89999999999998)),
    )
