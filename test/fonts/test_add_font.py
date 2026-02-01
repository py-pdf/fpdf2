from os import devnull
import sys
from pathlib import Path

import pytest

from fpdf import FPDF
from fontTools.ttLib import TTCollection, woff2
from test.conftest import LOREM_IPSUM, assert_pdf_equal, assert_same_file

HERE = Path(__file__).resolve().parent


def test_add_font_non_existing_file():
    pdf = FPDF()
    with pytest.raises(FileNotFoundError) as error:
        pdf.add_font(fname="non-existing-file.ttf")
    assert str(error.value) == "TTF Font file not found: non-existing-file.ttf"


def test_add_font_pkl():
    pdf = FPDF()
    with pytest.raises(ValueError) as error:
        pdf.add_font(fname="non-existing-file.pkl")
    assert str(error.value) == (
        "Unsupported font file extension: .pkl. add_font() used to accept .pkl file as input, "
        "but for security reasons this feature is deprecated since v2.5.1 and has been removed in v2.5.3."
    )


def test_deprecation_warning_for_FPDF_CACHE_DIR_and_FPDF_CACHE_MODE():
    # pylint: disable=import-outside-toplevel,pointless-statement,reimported
    from fpdf import fpdf

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_DIR
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_DIR = "/tmp"
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_MODE
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_MODE = 1
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    fpdf.SOME = 1
    assert fpdf.SOME == 1

    import fpdf

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_DIR
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_DIR = "/tmp"
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_MODE
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    with pytest.warns(DeprecationWarning) as record:
        fpdf.FPDF_CACHE_MODE = 1
    assert len(record) == 1
    assert_same_file(record[0].filename, __file__)

    fpdf.SOME = 1
    assert fpdf.SOME == 1


def test_add_font_with_str_fname_ok(tmp_path):
    font_file_path = str(HERE / "Roboto-Regular.ttf")
    for font_cache_dir in (True, str(tmp_path), None):
        with pytest.warns(DeprecationWarning) as record:
            pdf = FPDF(font_cache_dir=font_cache_dir)
            pdf.add_font(fname=font_file_path)
            pdf.set_font("Roboto-Regular", size=64)
            pdf.add_page()
            pdf.cell(text="Hello World!")
            assert_pdf_equal(pdf, HERE / "add_font_unicode.pdf", tmp_path)

        for r in record:
            if r.category == DeprecationWarning:
                assert_same_file(r.filename, __file__)


def test_add_core_fonts():
    font_file_path = HERE / "Roboto-Regular.ttf"
    pdf = FPDF()
    pdf.add_page()

    with pytest.warns(UserWarning) as record:  # "already added".
        pdf.add_font("Helvetica", fname=font_file_path)
        pdf.add_font("Helvetica", style="B", fname=font_file_path)
        pdf.add_font("helvetica", style="IB", fname=font_file_path)
        pdf.add_font("times", style="", fname=font_file_path)
        pdf.add_font("courier", fname=font_file_path)
        assert not pdf.fonts  # No fonts added, as all of them are core fonts

    for r in record:
        assert_same_file(r.filename, __file__)


def test_render_en_dash(tmp_path):  # issue-166
    pdf = FPDF()
    pdf.add_font(fname=HERE / "Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular", size=120)
    pdf.add_page()
    pdf.cell(w=pdf.epw, text="–")  # U+2013
    assert_pdf_equal(pdf, HERE / "render_en_dash.pdf", tmp_path)


def test_add_font_otf(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Quicksand", style="", fname=HERE / "Quicksand-Regular.otf")
    pdf.add_font("Quicksand", style="B", fname=HERE / "Quicksand-Bold.otf")
    pdf.add_font("Quicksand", style="I", fname=HERE / "Quicksand-Italic.otf")
    pdf.set_font("Quicksand", size=32)
    text = (
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True)
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "fonts_otf.pdf", tmp_path)


def test_add_font_uppercase():
    pdf = FPDF()
    pdf.add_font(fname=HERE / "Roboto-BoldItalic.TTF")
    assert pdf.fonts is not None and len(pdf.fonts) != 0  # fonts add successful


def test_add_font_missing_notdef_glyph(caplog):
    pdf = FPDF()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular-without-notdef.ttf")
    assert pdf.fonts is not None and len(pdf.fonts) != 0  # fonts add successful
    assert (
        "TrueType Font 'roboto' is missing the '.notdef' glyph. "
        "Fallback glyph will be provided."
    ) in caplog.text


def test_font_missing_glyphs(caplog):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.set_font("Roboto")
    pdf.cell(text="Test 𝕥𝕖𝕤𝕥 🆃🅴🆂🆃 😲")
    pdf.output(devnull)
    assert (
        "Roboto is missing the following glyphs: "
        "'𝕥' (\\U0001d565), '𝕖' (\\U0001d556), '𝕤' (\\U0001d564), "
        "'🆃' (\\U0001f183), '🅴' (\\U0001f174), '🆂' (\\U0001f182), '😲' (\\U0001f632)"
        in caplog.text
    )


def test_font_with_more_than_10_missing_glyphs(caplog):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(family="Roboto", fname=HERE / "Roboto-Regular.ttf")
    pdf.set_font("Roboto")
    pdf.cell(
        text="Ogham space mark: '\U00001680' - Ideographic space: '\U00003000' - 𝒯ℰ𝒮𝒯 ⓉⒺⓈⓉ 𝕥𝕖𝕤𝕥 🆃🅴🆂🆃 🇹🇪🇸🇹"
    )
    pdf.output(devnull)
    assert (
        "Roboto is missing the following glyphs: "
        "' ' (\\u1680), '　' (\\u3000), "
        "'𝒯' (\\U0001d4af), 'ℰ' (\\u2130), '𝒮' (\\U0001d4ae), "
        "'Ⓣ' (\\u24c9), 'Ⓔ' (\\u24ba), 'Ⓢ' (\\u24c8), "
        "'𝕥' (\\U0001d565), '𝕖' (\\U0001d556), ... (and 7 others)" in caplog.text
    )


def test_add_font_woff(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Noto", style="", fname=HERE / "noto-sans-v42-latin-regular.woff")
    pdf.set_font("Noto", size=32)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "font_woff.pdf", tmp_path)


def test_add_font_woff_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Noto", style="", fname=HERE / "noto-sans-v42-latin-regular.woff")
    pdf.set_font("Noto", size=32)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "font_woff_hb.pdf", tmp_path)


def test_add_font_woff2(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Noto", style="", fname=HERE / "noto-sans-v42-latin-regular.woff2")
    pdf.set_font("Noto", size=32)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "font_woff2.pdf", tmp_path)


def test_add_font_woff2_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Noto", style="", fname=HERE / "noto-sans-v42-latin-regular.woff2")
    pdf.set_font("Noto", size=32)
    pdf.set_text_shaping(True)
    pdf.multi_cell(w=pdf.epw, text=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "font_woff2_hb.pdf", tmp_path)


def test_add_font_woff2_without_brotli(monkeypatch):
    monkeypatch.setattr(woff2, "haveBrotli", False, raising=True)

    pdf = FPDF()
    with pytest.raises(
        RuntimeError,
        match=r"^Could not open WOFF2 font\. WOFF2 support requires an external Brotli",
    ):
        pdf.add_font("Noto", style="", fname=HERE / "noto-sans-v42-latin-regular.woff2")


def test_add_font_collection_all_faces(tmp_path):
    """
    This test will render all faces in the NotoSansCJK font collection.
    This font has multiple faces for the same glyphs, with regional variations
    for Chinese, Japanese, and Korean.
    The output PDF will show the glyphs with those slight regional variations.
    """
    COLLECTION_FONT = HERE / "NotoSansCJK-Regular.ttc"
    COLLECTION_TEXT_ALL_FACES = "\u7e9b\u88ef\u8b56\u8c41\u904d\u98ef"
    pdf = FPDF()
    pdf.add_page()
    collection = TTCollection(str(COLLECTION_FONT))
    face_count = len(collection.fonts)
    for face_number in range(face_count):
        family = f"NotoCJKFace{face_number}"
        pdf.add_font(
            family=family,
            style="",
            fname=COLLECTION_FONT,
            collection_font_number=face_number,
        )
        pdf.set_font("helvetica", size=12)
        pdf.cell(text=f"Face {face_number}: ")
        pdf.set_font(family, size=12)
        pdf.cell(text=COLLECTION_TEXT_ALL_FACES)
        pdf.ln()
    assert_pdf_equal(pdf, HERE / "collection_all_faces.pdf", tmp_path)


def test_add_font_collection_shaping(tmp_path):
    """
    This test will render all faces in the NotoSansCJK font collection.
    This font has multiple faces for the same glyphs, with regional variations
    for Chinese, Japanese, and Korean.
    The output PDF will show the glyphs with those slight regional variations.
    """
    COLLECTION_FONT = HERE / "NotoSansCJK-Regular.ttc"
    COLLECTION_TEXT_ALL_FACES = "\u7e9b\u88ef\u8b56\u8c41\u904d\u98ef"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_text_shaping(True)
    collection = TTCollection(str(COLLECTION_FONT))
    face_count = len(collection.fonts)
    for face_number in range(face_count):
        family = f"NotoCJKFace{face_number}"
        pdf.add_font(
            family=family,
            style="",
            fname=COLLECTION_FONT,
            collection_font_number=face_number,
        )
        pdf.set_font("helvetica", size=12)
        pdf.cell(text=f"Face {face_number}: ")
        pdf.set_font(family, size=12)
        pdf.cell(text=COLLECTION_TEXT_ALL_FACES)
        pdf.ln()
    assert_pdf_equal(pdf, HERE / "collection_all_faces_shaping.pdf", tmp_path)


SYMBOL_FONT_PATH = Path(r"c:\Windows\Fonts\symbol.ttf")


@pytest.mark.skipif(
    sys.platform not in ("cygwin", "win32"), reason="Windows-only symbol font test"
)
@pytest.mark.skipif(not SYMBOL_FONT_PATH.exists(), reason="symbol.ttf not available")
def test_add_font_symbol(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("MSSymbol", style="", fname=SYMBOL_FONT_PATH)
    pdf.set_font("MSSymbol", size=32)
    pdf.set_text_shaping(True)
    pdf.multi_cell(
        w=pdf.epw,
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    )
    assert_pdf_equal(pdf, HERE / "symbol.pdf", tmp_path)


@pytest.mark.skipif(
    sys.platform not in ("cygwin", "win32"), reason="Windows-only symbol font test"
)
@pytest.mark.skipif(not SYMBOL_FONT_PATH.exists(), reason="symbol.ttf not available")
def test_add_font_symbol_shaping(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("MSSymbol", style="", fname=SYMBOL_FONT_PATH)
    pdf.set_font("MSSymbol", size=32)
    pdf.set_text_shaping(True)
    pdf.multi_cell(
        w=pdf.epw,
        text="ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz\n0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    )
    assert_pdf_equal(pdf, HERE / "symbol_shaping.pdf", tmp_path)
