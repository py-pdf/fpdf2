from fpdf import FPDF
from fpdf.line_break import Fragment, MultiLineBreak, text_line


def test_one_line():
    pdf = FPDF()
    pdf.set_font("Times", size=32)
    fragments = [
        Fragment.from_string("hello world", "", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, pdf.get_normalized_string_width_with_style
    )
    assert multi_line_break.get_line_of_given_width(100000) == text_line(
        fragments, 4583, 1, False
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_two_lines():
    pdf = FPDF()
    pdf.set_font("Times", size=32)
    fragments = [
        Fragment.from_string("hello world", "", False),
    ]

    multi_line_break = MultiLineBreak(
        fragments, pdf.get_normalized_string_width_with_style
    )
    assert multi_line_break.get_line_of_given_width(2500) == text_line(
        [Fragment.from_string("hello", "", False)], 2000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(2500) == text_line(
        [Fragment.from_string("world", "", False)], 2333, 0, False
    )
    assert multi_line_break.get_line_of_given_width(2500) is None


def test_custom_font():
    alphabet = {
        "normal": {},
        "bold": {},
    }
    for char in "hello world":
        alphabet["normal"][char] = 500
        alphabet["bold"][char] = 1000

    fragments = [
        Fragment.from_string("hello ", "normal", False),
        Fragment.from_string("world", "bold", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(2500) == text_line(
        [Fragment.from_string("hello", "normal", False)], 2500, 0, False
    )
    assert multi_line_break.get_line_of_given_width(6000) == text_line(
        [Fragment.from_string("world", "bold", False)], 5000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(6000) is None


def test_custom_soft_hyphen():
    alphabet = {
        "normal": {"\u002d": 500},
    }
    long_string = "\u00ad".join("abcdefghijklmnop")
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(2500) == text_line(
        [Fragment.from_string("abcd\u002d", "normal", False)], 2500, 0, False
    )
    assert multi_line_break.get_line_of_given_width(2500) == text_line(
        [Fragment.from_string("efgh\u002d", "normal", False)], 2500, 0, False
    )
    assert multi_line_break.get_line_of_given_width(2200) == text_line(
        [Fragment.from_string("ijk\u002d", "normal", False)], 2000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(1000) == text_line(
        [Fragment.from_string("l\u002d", "normal", False)], 1000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(1000) == text_line(
        [Fragment.from_string("m\u002d", "normal", False)], 1000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(1000) == text_line(
        [Fragment.from_string("n\u002d", "normal", False)], 1000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(1000) == text_line(
        [Fragment.from_string("op", "normal", False)], 1000, 0, False
    )
    assert multi_line_break.get_line_of_given_width(1000) is None
