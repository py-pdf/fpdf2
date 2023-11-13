from pathlib import Path

from fpdf import FPDF
from fpdf.bidi import BidiParagraph, auto_detect_base_direction
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

# The BidiTest.txt file lists the input string as a list of character classes.
# CHAR_MAPPING is mapping one character of each class so we can test the algorithm with a string.
# i.e. translate L ET CS ON to "a$,!"
CHAR_MAPPING = {
    "AL": "\u0608",  # Arabic Letter
    "AN": "\u0600",  # Arabic Number
    "B": "\u2029",  # Paragraph Separator
    "BN": "\U000e007a",  # Boundary Neutral
    "CS": ",",  # Common Separator
    "EN": "0",  # European Number
    "ES": "+",  # European Separator
    "ET": "$",  # European Terminator
    "FSI": "\u2068",  # First Strong Isolate
    "L": "a",  # Left-to-right
    "NSM": "\u0303",  # Nonspacing Mark
    "R": "\u05be",  # Right-to-left
    "LRE": "\u202a",  # Left-to-Right Embedding
    "LRI": "\u2066",  # Left-to-Right Isolate
    "LRO": "\u202d",  # Left-to-Right Override
    "ON": "!",  # Other Neutrals
    "PDF": "\u202c",  # Pop Directional Format
    "PDI": "\u2069",  # Pop Directional Isolate
    "RLE": "\u202b",  # Right-to-Left Embedding
    "RLI": "\u2067",  # Right-to-Left Isolate
    "RLO": "\u202e",  # Right-to-Left Override
    "S": "\t",  # Segment Separator
    "WS": " ",  # White Space
}


def test_bidi_conformance():
    """
    The file BidiTest.txt comprises exhaustive test sequences of bidirectional types
    https://www.unicode.org/reports/tr41/tr41-32.html#Tests9
    This file contais 770,241 tests
    """

    def check_result(string, base_direction, levels, reorder):
        characters, reordered_characters = BidiParagraph(
            text=string, base_direction=base_direction
        ).get_all()
        levels = [i for i in levels if i != "x"]
        if not levels:
            len_levels = 0
        else:
            len_levels = len(levels)
        if len(characters) != len_levels:
            return False
        for indx, char in enumerate(characters):
            if levels[indx] != "x" and levels[indx] != str(char.embedding_level):
                return False
        return not any(
            reorder[indx] != str(char.character_index)
            for (indx, char) in enumerate(reordered_characters)
        )

    with open(HERE / "BidiTest.txt", "r", encoding="utf8") as f:
        data = f.read().split("\n")

    levels = []
    reorder = []
    test_count = 0
    for line in data:
        if len(line) == 0:  # ignore blank line
            continue
        if line[0] == "#":  # ignore comment line
            continue
        if line.startswith("@Levels:"):
            levels = line[9:].split(" ")
            continue
        if line.startswith("@Reorder:"):
            reorder = line[10:].split(" ")
            continue
        test_data = line.split(";")
        assert len(test_data) == 2

        string = ""
        for char_type in test_data[0].split(" "):
            string += CHAR_MAPPING[char_type]

        bitset = test_data[1]
        if int(bitset) & 1 > 0:  # auto-detect
            assert check_result(string, None, levels, reorder)
            test_count += 1
        if int(bitset) & 2 > 0:  # force LTR
            assert check_result(string, "L", levels, reorder)
            test_count += 1
        if int(bitset) & 4 > 0:  # force RTL
            assert check_result(string, "R", levels, reorder)
            test_count += 1
    assert test_count == 770241


def test_bidi_character():
    """
    The other test file, BidiCharacterTest.txt, contains test sequences of explicit code points, including, for example, bracket pairs.
    There are 91,707 tests on this file
    """

    with open(HERE / "BidiCharacterTest.txt", "r", encoding="utf8") as f:
        data = f.read().split("\n")

    test_count = 0
    for line in data:
        if len(line) == 0:  # ignore blank line
            continue
        if line[0] == "#":  # ignore comment line
            continue
        test_data = line.split(";")
        assert len(test_data) == 5
        test_count += 1

        string = ""
        for char in test_data[0].split(" "):
            string += chr(int(char, 16))
        assert test_data[1] in ("0", "1", "2")
        if test_data[1] == "0":
            base_direction = "L"
        elif test_data[1] == "1":
            base_direction = "R"
        elif test_data[1] == "2":
            base_direction = None  # auto

        if not base_direction:
            # test the auto detect direction algorithm
            assert (
                auto_detect_base_direction(string) == "L" and test_data[2] == "0"
            ) or (auto_detect_base_direction(string) == "R" and test_data[2] == "1")

        characters = BidiParagraph(
            text=string, base_direction=base_direction
        ).get_characters()

        result_index = 0
        for level in test_data[3].split(" "):
            if level == "x":
                continue
            assert int(level) == characters[result_index].embedding_level
            result_index += 1

    assert test_count == 91707


def test_bidi_string(tmp_path):
    # pylint: disable=bidirectional-unicode
    string = (
        "عندما يريد العالم أن ‪يتكلّم ‬ ،"
        + " فهو يتحدّث بلغة يونيكود. تسجّل الآن لحضور المؤتمر الدولي العاشر ليونيكود (Unicode Conference)، "
        + "الذي سيعقد في 10-12 آذار 1997 بمدينة مَايِنْتْس، ألمانيا. و سيجمع المؤتمر بين خبراء من كافة قطاعات الصناعة على الشبكة"
        + " العالمية انترنيت ويونيكود، حيث ستتم، على الصعيدين الدولي والمحلي على حد سواء مناقشة سبل استخدام"
        + " يونكود في النظم القائمة وفيما يخص التطبيقات الحاسوبية، الخطوط، تصميم النصوص والحوسبة متعددة اللغات."
    )
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="NotoSansArabic", fname=HERE / "NotoSansArabic-Regular.ttf")
    pdf.add_font(family="NotoSans", fname=HERE / "NotoSans-Regular.ttf")
    pdf.set_fallback_fonts(["NotoSans"])
    pdf.set_font("NotoSansArabic", size=20)
    pdf.set_text_shaping(False)
    pdf.multi_cell(text=string, w=pdf.epw, h=10, new_x="LEFT", new_y="NEXT", align="R")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.multi_cell(text=string, w=pdf.epw, h=10, new_x="LEFT", new_y="NEXT", align="R")

    assert_pdf_equal(
        pdf,
        HERE / "bidi_arabic.pdf",
        tmp_path,
    )
