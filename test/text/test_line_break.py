from fpdf import FPDFException
from fpdf.line_break import Fragment, MultiLineBreak, TextLine

import pytest


def test_no_fragments():
    """
    There is no text provided to break into multiple lines
    expected behavior ->
        - call to `get_line_of_given_width` always returns None
    """
    char_width = 6
    test_width = char_width * 200
    alphabet = {
        "normal": {},
    }
    multi_line_break = MultiLineBreak(
        [],
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    assert multi_line_break.get_line_of_given_width(test_width) is None
    assert multi_line_break.get_line_of_given_width(char_width) is None


def test_width_calculation():
    """
    Every character has different width
    """
    text = "abcd"
    char_width = 2
    alphabet = {
        "normal": {},
    }
    for i, char in enumerate(text):
        alphabet["normal"][char] = char_width + i
    fragments = [
        Fragment(text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )

    # zero width returns empty line
    res = multi_line_break.get_line_of_given_width(0)
    exp = TextLine(
        fragments=[],
        text_width=0,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp

    # the first character has width of char_width.
    # request of 1 unit line raises an exception
    with pytest.raises(FPDFException):
        res = multi_line_break.get_line_of_given_width(1)

    # get other characters one by one
    for i, char in enumerate(text):
        res = multi_line_break.get_line_of_given_width(char_width + i)
        exp = TextLine(
            fragments=[Fragment(char, "normal", False)],
            text_width=char_width + i,
            number_of_spaces_between_words=0,
            justify=False,
            trailing_nl=False,
        )
        assert res == exp

    res = multi_line_break.get_line_of_given_width(100000)
    exp = None
    assert res == exp


def test_single_space_in_fragment():
    """
    there is only one space character in the input text.
    expected behavior ->
        - first call to `get_line_of_given_width` contains space.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = " "
    char_width = 6
    test_width = char_width * 10
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=fragments,
        text_width=char_width,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(100000)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width = char_width * 200
    fragments = [
        Fragment(text, "normal", False),
    ]
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width = char_width * 4
    fragments = [
        Fragment(text, "normal", False),
    ]
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=fragments,
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_real_hyphen_acts_differently_from_soft_hyphen():
    words = ["a", "b", "c", "d"]
    char_width = 6
    test_width = char_width * 4
    alphabet = {
        "normal": {"\u002d": char_width},
    }
    words_separated_by_soft_hyphen = "\u00ad".join(words)
    words_separated_by_hard_hyphen = "\u002d".join(words)
    for char in words_separated_by_soft_hyphen:
        alphabet["normal"][char] = char_width
    soft_hyphen_line_break = MultiLineBreak(
        [Fragment(words_separated_by_soft_hyphen, "normal", False)],
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    hard_hyphen_line_break = MultiLineBreak(
        [Fragment(words_separated_by_hard_hyphen, "normal", False)],
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    hh_res = soft_hyphen_line_break.get_line_of_given_width(test_width)
    sh_res = hard_hyphen_line_break.get_line_of_given_width(test_width)
    assert hh_res != sh_res
    hh_res = soft_hyphen_line_break.get_line_of_given_width(test_width)
    sh_res = hard_hyphen_line_break.get_line_of_given_width(test_width)
    assert hh_res != sh_res


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
    char_width = 6
    test_width = char_width * 10
    test_width_B = char_width * 5
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {"\u002d": char_width},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("hello", "normal", False)],
        text_width=test_width_B,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_trailing_whitespace():
    """
    fit one word and trailing whitespace into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains the word and the space.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello "
    char_width = 6
    test_width = char_width * 10
    test_width_B = char_width * 6
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=fragments,
        text_width=test_width_B,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_two_words_one_line():
    """
    fit two words into the line with extremely large width.
    expected behavior ->
        - first call to `get_line_of_given_width` cointains all words.
        - second call to `get_line_of_given_width` is None because there is no
            text left.
    """
    text = "hello world"
    char_width = 6
    test_width = char_width * 200
    test_width_B = char_width * 11
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=fragments,
        text_width=test_width_B,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width = char_width * 200
    test_width_B = char_width * 11
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=fragments,
        text_width=test_width_B,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width = char_width * 5
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width

    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("hello", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("world", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width = char_width * 5
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )

    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("hello", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("world", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width_A = char_width * 12
    test_width_AA = char_width * 11
    text = " ".join([first_line_text, second_line_text])
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width

    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[Fragment(first_line_text, "normal", False)],
        text_width=test_width_AA,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[Fragment(second_line_text, "normal", False)],
        text_width=test_width_AA,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = None
    assert res == exp


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
    char_width = 6
    test_width_A = char_width * 12
    test_width_AA = char_width * 11
    text = " ".join((first_line_text, second_line_text))
    fragments = [
        Fragment(text, "normal", False),
    ]
    alphabet = {
        "normal": {},
    }
    for char in text:
        alphabet["normal"][char] = char_width

    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[Fragment(first_line_text, "normal", False)],
        text_width=test_width_AA,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[Fragment(second_line_text, "normal", False)],
        text_width=test_width_AA,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = None
    assert res == exp


def test_break_fragment_into_two_lines():
    """
    There are multiple fragments with different styles.
    This test breaks one fragment between two lines.
    """
    char_width = 6
    charB_width = 12
    test_width_A = char_width * 10
    test_width_B = char_width * 16
    test_width_BB = char_width * 15
    alphabet = {
        "normal": {},
        "bold": {},
    }
    first_line_text = "one "
    second_line_text = "two three"
    third_line_text = " four"
    text = "".join((first_line_text, second_line_text, third_line_text))
    for char in text:
        alphabet["normal"][char] = char_width
        alphabet["bold"][char] = charB_width

    fragments = [
        Fragment(first_line_text, "normal", False),
        Fragment(second_line_text, "bold", False),
        Fragment(third_line_text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[
            Fragment(first_line_text, "normal", False),
            Fragment("two", "bold", False),
        ],
        text_width=test_width_A,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[
            Fragment("three", "bold", False),
            Fragment(third_line_text, "normal", False),
        ],
        text_width=test_width_BB,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = None
    assert res == exp


def test_break_fragment_into_two_lines_justify():
    """
    There are multiple fragments with different styles.
    This test breaks one fragment between two lines.
    """
    char_width = 6
    charB_width = 12
    test_width_A = char_width * 10
    test_width_B = char_width * 16
    test_width_BB = char_width * 15
    alphabet = {
        "normal": {},
        "bold": {},
    }
    first_line_text = "one "
    second_line_text = "two three"
    third_line_text = " four"
    text = "".join((first_line_text, second_line_text, third_line_text))
    for char in text:
        alphabet["normal"][char] = char_width
        alphabet["bold"][char] = charB_width

    fragments = [
        Fragment(first_line_text, "normal", False),
        Fragment(second_line_text, "bold", False),
        Fragment(third_line_text, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[
            Fragment(first_line_text, "normal", False),
            Fragment("two", "bold", False),
        ],
        text_width=test_width_A,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[
            Fragment("three", "bold", False),
            Fragment(third_line_text, "normal", False),
        ],
        text_width=test_width_BB,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = None
    assert res == exp


def test_soft_hyphen_break():
    """
    all characters are separated by soft-hyphen
    expected behavior - there is a hard hyphen at the end of every line,
    except of the last one
    """
    char_width = 6
    test_width = char_width * 5
    test_width_A = char_width * 4.4
    test_width_AA = char_width * 4
    test_width_B = char_width * 2
    alphabet = {"normal": {"\u002d": char_width}}
    long_string = "\u00ad".join("abcdefghijklmnop")
    for char in long_string:
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("abcd\u002d", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("efgh\u002d", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_A)
    exp = TextLine(
        fragments=[Fragment("ijk\u002d", "normal", False)],
        text_width=test_width_AA,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[Fragment("l\u002d", "normal", False)],
        text_width=test_width_B,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[Fragment("m\u002d", "normal", False)],
        text_width=test_width_B,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[Fragment("n\u002d", "normal", False)],
        text_width=test_width_B,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = TextLine(
        fragments=[Fragment("op", "normal", False)],
        text_width=test_width_B,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width_B)
    exp = None
    assert res == exp


def test_soft_hyphen_break_justify():
    """
    all characters are separated by soft-hyphen
    expected behavior - there is a hard hyphen at the end of every line,
    except of the last one
    """
    char_width = 6
    test_width = char_width * 6
    last_width = char_width * 5
    alphabet = {"normal": {"\u002d": char_width}}
    words = ["ab cd", "ef gh", "kl mn"]
    long_string = "\u00ad".join(words)
    for char in long_string:
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("ab cd\u002d", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("ef gh\u002d", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=1,
        justify=True,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("kl mn", "normal", False)],
        text_width=last_width,
        number_of_spaces_between_words=1,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_explicit_break():
    """
    There is an explicit break character after every character
    Expected behavior:
        `get_line_of_given_width` returns single character on every call
    """
    char_width = 6
    test_width = char_width * 5
    alphabet = {
        "normal": {},
    }
    long_string = "\n".join("abcd")
    for char in long_string:
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("a", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("b", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("c", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("d", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_explicit_break_justify():
    """
    There is an explicit break character after every character
    Expected behavior:
        `get_line_of_given_width` returns single character on every call,
        returned lines are expected to be unjustified
    """
    char_width = 6
    test_width = char_width * 5
    alphabet = {
        "normal": {},
    }
    long_string = "\n".join("abcd")
    for char in long_string:
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("a", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("b", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("c", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=True,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("d", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_single_word_doesnt_fit_into_width():
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
    char_width = 6
    test_width = char_width * 5
    for char in long_string:
        # glyph space units
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("abcde", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("fghij", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("klmno", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("p", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(1000)
    exp = None
    assert res == exp


def test_single_word_doesnt_fit_into_width_justify():
    """
    There is a single word that doesn't fit into requested line
    Expected behavior:
        `get_line_of_given_width` as much characters as can fit into user
        provided width. returned lines are expected to be unjustified
    """
    char_width = 6
    test_width = char_width * 5
    alphabet = {
        "normal": {},
    }
    long_string = "abcdefghijklmnop"
    for char in long_string:
        # glyph space units
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("abcde", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("fghij", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("klmno", "normal", False)],
        text_width=test_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = TextLine(
        fragments=[Fragment("p", "normal", False)],
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,
        trailing_nl=False,
    )
    res = multi_line_break.get_line_of_given_width(test_width)
    exp = None
    assert res == exp


def test_last_line_no_justify():
    """
    Make sure that the last line is not justified.
    """
    alphabet = {
        "normal": {},
    }
    long_string = "a"
    char_width = 6
    for char in long_string:
        # glyph space units
        alphabet["normal"][char] = char_width

    fragments = [
        Fragment(long_string, "normal", False),
    ]
    multi_line_break = MultiLineBreak(
        fragments,
        lambda a, b, font_size=None, font_family=None, font_stretching=None, char_spacing=None: alphabet[
            b
        ][a],
        justify=True,
    )
    res = multi_line_break.get_line_of_given_width(char_width * 5)
    exp = TextLine(
        fragments=fragments,
        text_width=char_width,
        number_of_spaces_between_words=0,
        justify=False,  # !
        trailing_nl=False,
    )
    assert res == exp
    res = multi_line_break.get_line_of_given_width(char_width)
    exp = None
    assert res == exp
