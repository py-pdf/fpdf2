from pathlib import Path

from fpdf import FPDF
from fpdf.unicode_script import get_unicode_script, UnicodeScript
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_indi_text(tmp_path):  # issue #365
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Mangal", fname=HERE / "Mangal 400.ttf")
    pdf.set_font("Mangal", size=40)
    pdf.set_text_shaping(False)
    pdf.cell(text="इण्टरनेट पर हिन्दी के साधन", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(text="इण्टरनेट पर हिन्दी के साधन", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "shaping_hindi.pdf", tmp_path)


def test_mixed_text_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.r_margin = 100
    pdf.add_font(
        family="KFGQPC", fname=HERE / "KFGQPC Uthmanic Script HAFS Regular.otf"
    )
    pdf.set_font("KFGQPC", size=36)
    pdf.set_text_shaping(True)
    pdf.write(text="مثال على اللغة العربية. محاذاة لليمين.")
    pdf.add_font(family="Mangal", fname=HERE / "Mangal 400.ttf")
    pdf.set_font("Mangal", size=40)
    # With preceding whitespace
    pdf.write(text=" इण्टरनेट पर हिन्दी के साधन")

    assert_pdf_equal(pdf, HERE / "text_mixed_text_shaping.pdf", tmp_path)


def test_text_replacement(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="FiraCode", fname=HERE / "FiraCode-Regular.ttf")
    pdf.set_font("FiraCode", size=40)
    pdf.set_text_shaping(False)
    pdf.cell(text="http://www 3 >= 2 != 1", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(text="http://www 3 >= 2 != 1", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "text_replacement.pdf", tmp_path)


def test_kerning(tmp_path):  # issue #812
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Dumbledor3Thin", fname=HERE / "Dumbledor3Thin.ttf")
    pdf.set_font("Dumbledor3Thin", size=40)
    pdf.set_text_shaping(False)
    pdf.cell(text="Ты То Тф Та Тт Ти", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(text="Ты То Тф Та Тт Ти", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "kerning.pdf", tmp_path)


def test_hebrew_diacritics(tmp_path):  # issue #549
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="SBL_Hbrw", fname=HERE / "SBL_Hbrw.ttf")
    pdf.set_font("SBL_Hbrw", size=40)
    pdf.set_text_shaping(False)
    pdf.cell(text="בּ", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(text="בּ", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "hebrew_diacritics.pdf", tmp_path)


def test_ligatures(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="ViaodaLibre", fname=HERE / "ViaodaLibre-Regular.ttf")
    pdf.set_font("ViaodaLibre", size=40)
    pdf.set_text_shaping(False)
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "ligatures.pdf", tmp_path)


def test_arabic_right_to_left(tmp_path):  # issue #549
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(
        family="KFGQPC", fname=HERE / "KFGQPC Uthmanic Script HAFS Regular.otf"
    )
    pdf.set_font("KFGQPC", size=36)
    pdf.set_text_shaping(False)
    pdf.cell(text="مثال على اللغة العربية. محاذاة لليمين.", new_x="LEFT", new_y="NEXT")
    pdf.ln(36)
    pdf.set_text_shaping(True)
    pdf.cell(text="مثال على اللغة العربية. محاذاة لليمين.", new_x="LEFT", new_y="NEXT")

    assert_pdf_equal(pdf, HERE / "arabic.pdf", tmp_path)


def test_multi_cell_markdown_with_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    pdf.set_text_shaping(True)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_styling.pdf", tmp_path)


def test_features(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="ViaodaLibre", fname=HERE / "ViaodaLibre-Regular.ttf")
    pdf.set_font("ViaodaLibre", size=40)
    pdf.set_text_shaping(use_shaping_engine=True)
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(use_shaping_engine=True, features={"liga": False})
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(use_shaping_engine=True, features={"kern": False})
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(
        use_shaping_engine=True, direction="rtl", script="Latn", language="en-us"
    )
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()

    assert_pdf_equal(pdf, HERE / "features.pdf", tmp_path)


def test_text_with_parentheses(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="SBL_Hbrw", fname=HERE / "SBL_Hbrw.ttf")
    pdf.set_font("SBL_Hbrw", size=30)
    pdf.set_text_shaping(True)
    pdf.cell(text="אנגלית (באנגלית: English) ה", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.cell(text="אנגלית (באנגלית: English) ", new_y="NEXT")
    assert_pdf_equal(pdf, HERE / "text_with_parentheses.pdf", tmp_path)


def test_text_shaping_and_offset_rendering(tmp_path):  # issue #1075
    pdf = FPDF()
    pdf.add_font("Garuda", fname=FONTS_DIR / "Garuda.ttf")
    pdf.set_font("Garuda", size=16)
    pdf.set_text_shaping(True)
    pdf.add_page()
    line_height, col_width = pdf.font_size * 2, pdf.epw / 4
    for i in range(2):
        with pdf.offset_rendering():
            pdf.cell(col_width, line_height, f"Cell ({i})")
        pdf.cell(col_width, line_height, f"Cell ({i})")
    assert_pdf_equal(pdf, HERE / "text_shaping_and_offset_rendering.pdf", tmp_path)


def test_multilingual_string(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="KhmerOS", fname=HERE / "KhmerOS.ttf")
    pdf.set_font("KhmerOS", size=30)
    pdf.set_text_shaping(True)
    pdf.cell(text="Khmer: សួស្តី ពិភពលោក")
    assert_pdf_equal(pdf, HERE / "multilingual_string.pdf", tmp_path)


def test_unicode_script_codes():
    char_list = (
        "\x03",
        "E",
        "Ͳ",
        "Ѧ",
        "Ւ",
        "ֲ",
        "\u0601",
        "܋",
        "ޔ",
        "ं",
        "ঀ",
        "ਁ",
        "ઁ",
        "ଁ",
        "ஂ",
        "ఀ",
        "ಀ",
        "ഁ",
        "ඁ",
        "พ",
        "ຂ",
        "ༀ",
        "ဦ",
        "Ⴔ",
        "ᆙ",
        "ለ",
        "Ꭴ",
        "᐀",
        "\u1680",
        "ᚲ",
        "ឨ",
        "᠀",
        "を",
        "ケ",
        "˫",
        "⺁",
        "ꀑ",
        "𐌒",
        "𐌿",
        "𐐱",
        "̬",
        "ᜃ",
        "ᜬ",
        "ᝈ",
        "ᝡ",
        "ᤌ",
        "ᥢ",
        "𐀁",
        "𐎝",
        "𐑷",
        "𐒒",
        "𐠂",
        "⣫",
        "ᨏ",
        "ϯ",
        "ᦐ",
        "Ⰺ",
        "ⵎ",
        "ꠀ",
        "𐎧",
        "𐨀",
        "ᬀ",
        "𒉑",
        "𐤀",
        "ꡪ",
        "߂",
        "ᮁ",
        "ᰙ",
        "᱘",
        "ꗵ",
        "ꢁ",
        "꤈",
        "ꤲ",
        "𐊌",
        "𐊧",
        "𐤯",
        "ꨤ",
        "ᩂ",
        "ꪑ",
        "𐬏",
        "𓆊",
        "ࠍ",
        "ꓧ",
        "ꛆ",
        "ꦁ",
        "ꫪ",
        "𐡄",
        "𐩶",
        "𐭂",
        "𐭦",
        "𐰞",
        "𑂁",
        "ᯣ",
        "𑀀",
        "ࡍ",
        "𑄂",
        "𐦪",
        "𐦈",
        "𖼴",
        "𑆁",
        "𑃝",
        "𑚛",
        "𐕘",
        "𖫝",
        "𛱨",
        "𐔑",
        "𑌁",
        "𖬫",
        "𑈇",
        "𐙤",
        "𑅙",
        "𐫀",
        "𞠒",
        "𑘑",
        "𖩍",
        "𐪁",
        "𐢜",
        "𐡰",
        "𑫘",
        "𐍒",
        "𐮅",
        "𑖤",
        "𑋒",
        "𑒆",
        "𑣅",
        "𑜄",
        "𔕘",
        "𐣥",
        "𑊅",
        "𐲑",
        "𝣣",
        "𞥂",
        "𑰈",
        "𑱰",
        "𑐩",
        "𐒵",
        "𖿠",
        "𑴄",
        "𖿡",
        "𑩐",
        "𑨀",
        "𑠇",
        "𑵢",
        "𑻧",
        "𖹻",
        "𐴞",
        "𐼾",
        "𐼅",
        "𐿴",
        "𑦤",
        "𞄥",
        "𞋄",
        "𐾷",
        "𑤁",
        "𖿤",
        "𐺟",
        "𒿬",
        "𐽷",
        "𖪼",
        "𞊞",
        "𐕸",
        "\U00011f00",
        "\U0001e4d5",
    )
    for index, char in enumerate(char_list):
        assert get_unicode_script(char) == UnicodeScript(index)
    get_unicode_script.cache_clear()


def test_disabling_text_shaping(tmp_path):  # issue #1287
    pdf = FPDF()
    pdf.add_font(family="ViaodaLibre", fname=HERE / "ViaodaLibre-Regular.ttf")
    pdf.set_font("ViaodaLibre", size=24)
    pdf.add_page()
    assert not pdf.text_shaping
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    assert pdf.text_shaping
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(False)
    assert not pdf.text_shaping
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    pdf.set_text_shaping(True)
    assert pdf.text_shaping
    pdf.cell(text="final soft stuff", new_x="LEFT", new_y="NEXT")
    pdf.ln()
    assert_pdf_equal(pdf, HERE / "disabling_text_shaping.pdf", tmp_path)
