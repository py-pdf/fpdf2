from pathlib import Path
from urllib.request import urlopen

from fpdf import FPDF
from fpdf.bidi import BidiParagraph, auto_detect_base_direction
from fpdf.enums import TextDirection
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

    with urlopen(
        "https://www.unicode.org/Public/15.1.0/ucd/BidiTest.txt"
    ) as url_file:  # nosec B310
        data = url_file.read().decode("utf-8").split("\n")

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
            assert check_result(string, TextDirection.LTR, levels, reorder)
            test_count += 1
        if int(bitset) & 4 > 0:  # force RTL
            assert check_result(string, TextDirection.RTL, levels, reorder)
            test_count += 1
    assert test_count == 770241


def test_bidi_character():
    """
    The other test file, BidiCharacterTest.txt, contains test sequences of explicit code points, including, for example, bracket pairs.
    There are 91,707 tests on this file
    """

    with urlopen(
        "https://www.unicode.org/Public/15.1.0/ucd/BidiCharacterTest.txt"
    ) as url_file:  # nosec B310
        data = url_file.read().decode("utf-8").split("\n")

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
            base_direction = TextDirection.LTR
        elif test_data[1] == "1":
            base_direction = TextDirection.RTL
        elif test_data[1] == "2":
            base_direction = None  # auto

        if not base_direction:
            # test the auto detect direction algorithm
            assert (
                auto_detect_base_direction(string) == TextDirection.LTR
                and test_data[2] == "0"
            ) or (
                auto_detect_base_direction(string) == TextDirection.RTL
                and test_data[2] == "1"
            )

        characters = BidiParagraph(
            text=string, base_direction=base_direction
        ).get_characters_with_embedding_level()

        result_index = 0
        for level in test_data[3].split(" "):
            if level == "x":
                continue
            assert int(level) == characters[result_index].embedding_level
            result_index += 1

    assert test_count == 91707


def test_bidi_lorem_ipsum(tmp_path):
    # taken from https://ar.lipsum.com/ - contains Arabic (RTL) with portions in english (LTR) within the text
    ARABIC_LOREM_IPSUM = """
ما فائدته ؟
هناك حقيقة مثبتة منذ زمن طويل وهي أن المحتوى المقروء لصفحة ما سيلهي القارئ عن التركيز على الشكل الخارجي للنص أو شكل توضع الفقرات في الصفحة التي يقرأها. ولذلك يتم استخدام طريقة لوريم إيبسوم لأنها تعطي توزيعاَ طبيعياَ -إلى حد ما- للأحرف عوضاً عن استخدام "هنا يوجد محتوى نصي، هنا يوجد محتوى نصي" فتجعلها تبدو (أي الأحرف) وكأنها نص مقروء. العديد من برامح النشر المكتبي وبرامح تحرير صفحات الويب تستخدم لوريم إيبسوم بشكل إفتراضي كنموذج عن النص، وإذا قمت بإدخال "lorem ipsum" في أي محرك بحث ستظهر العديد من المواقع الحديثة العهد في نتائج البحث. على مدى السنين ظهرت نسخ جديدة ومختلفة من نص لوريم إيبسوم، أحياناً عن طريق الصدفة، وأحياناً عن عمد كإدخال بعض العبارات الفكاهية إليها.

ما أصله ؟
خلافاَ للإعتقاد السائد فإن لوريم إيبسوم ليس نصاَ عشوائياً، بل إن له جذور في الأدب اللاتيني الكلاسيكي منذ العام 45 قبل الميلاد، مما يجعله أكثر من 2000 عام في القدم. قام البروفيسور "ريتشارد ماك لينتوك" (Richard McClintock) وهو بروفيسور اللغة اللاتينية في جامعة هامبدن-سيدني في فيرجينيا بالبحث عن أصول كلمة لاتينية غامضة في نص لوريم إيبسوم وهي "consectetur"، وخلال تتبعه لهذه الكلمة في الأدب اللاتيني اكتشف المصدر الغير قابل للشك. فلقد اتضح أن كلمات نص لوريم إيبسوم تأتي من الأقسام 1.10.32 و 1.10.33 من كتاب "حول أقاصي الخير والشر" (de Finibus Bonorum et Malorum) للمفكر شيشيرون (Cicero) والذي كتبه في عام 45 قبل الميلاد. هذا الكتاب هو بمثابة مقالة علمية مطولة في نظرية الأخلاق، وكان له شعبية كبيرة في عصر النهضة. السطر الأول من لوريم إيبسوم "Lorem ipsum dolor sit amet.." يأتي من سطر في القسم 1.20.32 من هذا الكتاب.

للمهتمين قمنا بوضع نص لوريم إبسوم القياسي والمُستخدم منذ القرن الخامس عشر في الأسفل. وتم أيضاً توفير الأقسام 1.10.32 و 1.10.33 من "حول أقاصي الخير والشر" (de Finibus Bonorum et Malorum) لمؤلفه شيشيرون (Cicero) بصيغها الأصلية، مرفقة بالنسخ الإنكليزية لها والتي قام بترجمتها هـ.راكهام (H. Rackham) في عام 1914.

"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="NotoArabic", fname=HERE / "NotoNaskhArabic-Regular.ttf")
    pdf.add_font(family="NotoSans", fname=HERE / "NotoSans-Regular.ttf")
    pdf.set_fallback_fonts(["NotoSans"])
    pdf.set_font("NotoArabic", size=20)
    pdf.set_text_shaping(True)
    pdf.multi_cell(
        text=ARABIC_LOREM_IPSUM, w=pdf.epw, h=10, new_x="LEFT", new_y="NEXT", align="R"
    )

    assert_pdf_equal(
        pdf,
        HERE / "bidi_arabic_lorem_ipsum.pdf",
        tmp_path,
    )


def test_bidi_paragraph_direction(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="SBL_Hbrw", fname=HERE / "SBL_Hbrw.ttf")
    pdf.set_font("SBL_Hbrw", "", 18)

    text1 = "אנגלית (באנגלית: English)"  # first char is RTL
    text2 = "The test is: אנגלית (באנגלית: English)"  # first char is LTR

    pdf.cell(text="No text shaping (not bidirectional)", new_x="left", new_y="next")
    pdf.cell(text=text1, new_x="left", new_y="next")
    pdf.cell(text=text2, new_x="left", new_y="next")
    pdf.ln()

    pdf.set_text_shaping(use_shaping_engine=True)
    pdf.cell(
        text="Text shaping-Automatic paragraph direction", new_x="left", new_y="next"
    )
    pdf.cell(text=text1, new_x="left", new_y="next")
    pdf.cell(text=text2, new_x="left", new_y="next")
    pdf.ln()

    pdf.set_text_shaping(use_shaping_engine=True, direction="rtl")
    pdf.cell(
        text="Text shaping-Force paragraph direction RTL", new_x="left", new_y="next"
    )
    pdf.cell(text=text1, new_x="left", new_y="next")
    pdf.cell(text=text2, new_x="left", new_y="next")
    pdf.ln()

    pdf.set_text_shaping(use_shaping_engine=True, direction="ltr")
    pdf.cell(
        text="Text shaping-Force paragraph direction LTR", new_x="left", new_y="next"
    )
    pdf.cell(text=text1, new_x="left", new_y="next")
    pdf.cell(text=text2, new_x="left", new_y="next")
    pdf.ln()

    assert_pdf_equal(
        pdf,
        HERE / "bidi_paragraph_direction.pdf",
        tmp_path,
    )
