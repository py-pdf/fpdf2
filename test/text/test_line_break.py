from fpdf import FPDFException
from fpdf.line_break import Fragment, MultiLineBreak, TextLine

import pytest


def test_no_fragments():
    """
    There is no text provided to break into multiple lines
    expected behavior ->
        - call to `get_line_of_given_width` always returns None
    """
    alphabet = {
        "normal": {},
    }
    multi_line_break = MultiLineBreak([], lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(100000) is None
    assert multi_line_break.get_line_of_given_width(1) is None


def test_width_calculation():
    """
    Every character has different width
    """
    text = "abcd"
    alphabet = {
        "normal": {},
    }
    for width, char in enumerate(text):
        alphabet["normal"][char] = width + 2
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])

    # zero width returns empty line
    assert multi_line_break.get_line_of_given_width(0) == TextLine(
        fragments=[],
        text_width=0,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    # the first character has width of 2 units.
    # request of 1 unit line raises an exception
    with pytest.raises(FPDFException):
        multi_line_break.get_line_of_given_width(1)
    # get other characters one by one
    assert multi_line_break.get_line_of_given_width(2) == TextLine(
        fragments=[Fragment.from_string("a", "normal", False)],
        text_width=2,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(3) == TextLine(
        fragments=[Fragment.from_string("b", "normal", False)],
        text_width=3,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(4) == TextLine(
        fragments=[Fragment.from_string("c", "normal", False)],
        text_width=4,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(5) == TextLine(
        fragments=[Fragment.from_string("d", "normal", False)],
        text_width=5,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_single_space_in_fragment():
    """
    there is only one space character in the input text.
    expected behavior ->
        - first call to `get_line_of_given_width` contains space.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = " "
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=fragments,
        text_width=500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_single_soft_hyphen_in_fragment():
    """
    there is only one soft hyphen character in the input text.
    expected behavior ->
        - call to `get_line_of_given_width` always returns None, because soft
          hyphen doesn't break a word
    """
    alphabet = {
        "normal": {"\u002d": 500},
    }
    text = "\u00ad"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_single_hard_hyphen_in_fragment():
    """
    there is only one hard hyphen character in the input text.
    expected behavior ->
        - first call to `get_line_of_given_width` contains hard hyphen.
        - second call to `get_line_of_given_width` is None because there is no
    """
    alphabet = {
        "normal": {"\u002d": 500},
    }
    text = "\u002d"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=fragments,
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_real_hyphen_acts_differently_from_soft_hyphen():
    words = ["a", "b", "c", "d"]
    alphabet = {
        "normal": {"\u002d": 500},
    }
    words_separated_by_soft_hyphen = "\u00ad".join(words)
    words_separated_by_hard_hyphen = "\u002d".join(words)
    for char in words_separated_by_soft_hyphen:
        alphabet["normal"][char] = 500
    soft_hyphen_line_break = MultiLineBreak(
        [Fragment.from_string(words_separated_by_soft_hyphen, "normal", False)],
        lambda a, b: alphabet[b][a],
    )
    hard_hyphen_line_break = MultiLineBreak(
        [Fragment.from_string(words_separated_by_hard_hyphen, "normal", False)],
        lambda a, b: alphabet[b][a],
    )
    assert soft_hyphen_line_break.get_line_of_given_width(
        2000
    ) != hard_hyphen_line_break.get_line_of_given_width(2000)
    assert soft_hyphen_line_break.get_line_of_given_width(
        2000
    ) != hard_hyphen_line_break.get_line_of_given_width(2000)


def test_trailing_soft_hyphen():
    """
    fit one word and trailing soft-hyphen into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains the word.
          soft hyphen is not included in the line.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello\u00ad"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {"\u002d": 500},
    }
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=[Fragment.from_string("hello", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_trailing_whitespace():
    """
    fit one word and trailing whitespace into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains the word and the space.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello "
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=fragments,
        text_width=3000,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_two_words_one_line():
    """
    fit two words into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains all words.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello world"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(100000) == TextLine(
        fragments=fragments,
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_two_words_one_line_justify():
    """
    fit two words into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains all words.
            this line is expected to be unjustified, because it is the last
            line.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello world"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(100000) == TextLine(
        fragments=fragments,
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(100000) is None


def test_two_words_two_lines_break_by_space():
    """
    fit two words into the line that can fit only one word.
    expected behavior:
        - first call to `get_line_of_given_width` cointains the first word.
        - second call to `get_line_of_given_width` cointains the second word.
        - third call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello world"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500

    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("hello", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("world", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) is None


def test_two_words_two_lines_break_by_space_justify():
    """
    fit two words into the line that can fit only one word.
    expected behavior:
        - first call to `get_line_of_given_width` cointains the first word.
            Line is expected to be unjustified, because there are no spaces in
            the line.
        - second call to `get_line_of_given_width` cointains the second word.
            Line is expected to be unjustified, because it is the last line.
        - third call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello world"
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("hello", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("world", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) is None


def test_four_words_two_lines_break_by_space():
    """
    fit two words into the line that can fit only one word.
    expected behavior:
        - first call to `get_line_of_given_width` cointains the first word.
        - second call to `get_line_of_given_width` cointains the second word.
        - third call to `get_line_of_given_width` is None because there is no
            text left.
    """
    first_line_text = "hello world"
    second_line_text = "hello world"
    text = " ".join([first_line_text, second_line_text])
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500

    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(6000) == TextLine(
        fragments=[Fragment.from_string(first_line_text, "normal", False)],
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(6000) == TextLine(
        fragments=[Fragment.from_string(second_line_text, "normal", False)],
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) is None


def test_four_words_two_lines_break_by_space_justify():
    """
    fit two words into the line that can fit only one word.
    expected behavior:
        - first call to `get_line_of_given_width` cointains the first word.
            Line is expected to be justified.
        - second call to `get_line_of_given_width` cointains the second word.
            Line is expected to be unjustified, because it is the last line.
        - third call to `get_line_of_given_width` is None because there is no
            text left.
    """
    first_line_text = "hello world"
    second_line_text = "hello world"
    text = " ".join((first_line_text, second_line_text))
    fragments = [
        Fragment.from_string(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = 500

    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(6000) == TextLine(
        fragments=[Fragment.from_string(first_line_text, "normal", False)],
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(6000) == TextLine(
        fragments=[Fragment.from_string(second_line_text, "normal", False)],
        text_width=5500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) is None


def test_break_fragment_into_two_lines():
    """
    There are multiple fragments with different styles.
    This test breaks one fragment between two lines.
    """
    alphabet = {
        "normal": {},
        "bold": {},
    }
    first_line_text = "one "
    second_line_text = "two three"
    third_line_text = " four"
    text = "".join((first_line_text, second_line_text, third_line_text))
    for char in text:
        alphabet["normal"][char] = 500
        alphabet["bold"][char] = 1000

    fragments = [
        Fragment.from_string(first_line_text, "normal", False),
        Fragment.from_string(second_line_text, "bold", False),
        Fragment.from_string(third_line_text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=[
            Fragment.from_string(first_line_text, "normal", False),
            Fragment.from_string("two", "bold", False),
        ],
        text_width=5000,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(8000) == TextLine(
        fragments=[
            Fragment.from_string("three", "bold", False),
            Fragment.from_string(third_line_text, "normal", False),
        ],
        text_width=7500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(6000) is None


def test_break_fragment_into_two_lines_justify():
    """
    There are multiple fragments with different styles.
    This test breaks one fragment between two lines.
    """
    alphabet = {
        "normal": {},
        "bold": {},
    }
    first_line_text = "one "
    second_line_text = "two three"
    third_line_text = " four"
    text = "".join((first_line_text, second_line_text, third_line_text))
    for char in text:
        alphabet["normal"][char] = 500
        alphabet["bold"][char] = 1000

    fragments = [
        Fragment.from_string(first_line_text, "normal", False),
        Fragment.from_string(second_line_text, "bold", False),
        Fragment.from_string(third_line_text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(5000) == TextLine(
        fragments=[
            Fragment.from_string(first_line_text, "normal", False),
            Fragment.from_string("two", "bold", False),
        ],
        text_width=5000,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(8000) == TextLine(
        fragments=[
            Fragment.from_string("three", "bold", False),
            Fragment.from_string(third_line_text, "normal", False),
        ],
        text_width=7500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(6000) is None


def test_soft_hyphen_break():
    """
    all characters are separated by soft-hyphen
    expected behavior - there is a hard hyphen at the end of every line,
    except of the last one
    """
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
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("abcd\u002d", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("efgh\u002d", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2200) == TextLine(
        fragments=[Fragment.from_string("ijk\u002d", "normal", False)],
        text_width=2000,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) == TextLine(
        fragments=[Fragment.from_string("l\u002d", "normal", False)],
        text_width=1000,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) == TextLine(
        fragments=[Fragment.from_string("m\u002d", "normal", False)],
        text_width=1000,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) == TextLine(
        fragments=[Fragment.from_string("n\u002d", "normal", False)],
        text_width=1000,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) == TextLine(
        fragments=[Fragment.from_string("op", "normal", False)],
        text_width=1000,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_soft_hyphen_break_justify():
    """
    all characters are separated by soft-hyphen
    expected behavior - there is a hard hyphen at the end of every line,
    except of the last one
    """
    alphabet = {
        "normal": {"\u002d": 500},
    }
    words = ["ab cd", "ef gh", "kl mn"]
    long_string = "\u00ad".join(words)
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(3000) == TextLine(
        fragments=[Fragment.from_string("ab cd\u002d", "normal", False)],
        text_width=3000,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(3000) == TextLine(
        fragments=[Fragment.from_string("ef gh\u002d", "normal", False)],
        text_width=3000,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(3000) == TextLine(
        fragments=[Fragment.from_string("kl mn", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_explicit_break():
    """
    There is an explicit break character after every character
    Expected behavior:
        `get_line_of_given_width` returns single character on every call
    """
    alphabet = {
        "normal": {},
    }
    long_string = "\n".join("abcd")
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("a", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("b", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("c", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("d", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_explicit_break_justify():
    """
    There is an explicit break character after every character
    Expected behavior:
        `get_line_of_given_width` returns single character on every call,
        returned lines are expected to be unjustified
    """
    alphabet = {
        "normal": {},
    }
    long_string = "\n".join("abcd")
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("a", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("b", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("c", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("d", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_single_world_doesnt_fit_into_width():
    """
    There is a single word that doesn't fit into requested line
    Expected behavior:
        `get_line_of_given_width` as much characters as can fit into user
        provided width.
    """
    alphabet = {
        "normal": {},
    }
    long_string = "abcdefghijklmnop"
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(fragments, lambda a, b: alphabet[b][a])
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("abcde", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("fghij", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("klmno", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("p", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_single_world_doesnt_fit_into_width_justify():
    """
    There is a single word that doesn't fit into requested line
    Expected behavior:
        `get_line_of_given_width` as much characters as can fit into user
        provided width. returned lines are expected to be unjustified
    """
    alphabet = {
        "normal": {},
    }
    long_string = "abcdefghijklmnop"
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("abcde", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("fghij", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("klmno", "normal", False)],
        text_width=2500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=[Fragment.from_string("p", "normal", False)],
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None


def test_last_line_no_justify():
    """
    Make sure that the last line is not justified.
    """
    alphabet = {
        "normal": {},
    }
    long_string = "a"
    for char in long_string:
        alphabet["normal"][char] = 500

    fragments = [
        Fragment.from_string(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments, lambda a, b: alphabet[b][a], justify=True
    )
    assert multi_line_break.get_line_of_given_width(2500) == TextLine(
        fragments=fragments,
        text_width=500,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert multi_line_break.get_line_of_given_width(1000) is None
