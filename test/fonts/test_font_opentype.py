import re
from io import BytesIO
from pathlib import Path

import pypdf
from fontTools.cffLib import CFFFontSet
from fontTools.ttLib import TTFont

from fpdf import FPDF

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def _cmap_mappings(cmap):
    """Return the part of a CMap stream after its codespace range."""
    return cmap.get_object().get_data().split(b"endcodespacerange", 1)[1]


def test_cid_keyed_cff_font_embeds_cff_font_program(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Shsans", fname=HERE / "SourceHanSansCN-Normal.otf")

    pdf.set_font("Shsans", size=14)
    pdf.multi_cell(
        w=0,
        text=(
            "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Culpa labore "
            "quas fuga magnam, tempora repellendus ipsa, provident officiis adipisci "
            "modi ab perspiciatis ducimus pariatur dolor odio placeat odit atque? "
            "Aperiam. 天地玄黄 宇宙洪荒 日月盈昃 辰宿列张 寒来暑往 秋收冬藏 "
            "闰余成岁 律吕调阳"
        ),
    )

    assert_pdf_equal(
        pdf,
        HERE / "font_opentype.pdf",
        tmp_path,
    )


def test_name_keyed_cff_font_embeds_cff_font_program():
    # sample with some non-ASCII characters available in Quicksand
    text = "Hello world, Jürgen, François, José, Søren, Åsa, Þórunn, Ágnes and Zoë!"

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Quicksand", fname=HERE / "Quicksand-Regular.otf")
    pdf.set_font("Quicksand", size=12)
    pdf.cell(text=text)

    reader = pypdf.PdfReader(BytesIO(pdf.output()))

    # FontFile3 with subtype CIDFontType0C has been available since
    # PDF 1.3 (ISO 32000-1, 9.9), so the font must not raise the PDF
    # version
    assert reader.pdf_header == "%PDF-1.3"

    # Glyph descriptions based on CFF require a Type 0 CIDFont
    # (whereas a Type 2 CIDFont contains glyph descriptions based on
    # the TrueType format). A CIDToGIDMap is only allowed in a
    # CIDFontType2 (ISO 32000-1, 9.7.4.1)
    font = reader.pages[0]["/Resources"]["/Font"]["/F1"]
    cid_font = font["/DescendantFonts"][0].get_object()
    assert cid_font["/Subtype"] == "/CIDFontType0"
    assert "/CIDToGIDMap" not in cid_font

    # FontFile2 is reserved for TrueType font programs; a bare CFF
    # program for a CIDFontType0 belongs in FontFile3 with subtype
    # CIDFontType0C (ISO 32000-1, 9.9)
    descriptor = cid_font["/FontDescriptor"]
    assert "/FontFile2" not in descriptor
    font_file = descriptor["/FontFile3"].get_object()
    assert font_file["/Subtype"] == "/CIDFontType0C"

    # Other than the ToUnicode CMap (type 2), the encoding CMap maps
    # codes to CIDs, so it has type 1 (Adobe Technical Note #5099)
    encoding = font["/Encoding"].get_object()
    assert b"/CMapType 1 def" in encoding.get_data()

    # The CIDFont and its embedded encoding CMap must declare the same
    # character collection (ISO 19005-1, 6.3.3.1); CIDs of a name-keyed
    # CFF program are glyph indices, specific to the font
    keys = ("/Registry", "/Ordering", "/Supplement")
    cid_system_info = {key: cid_font["/CIDSystemInfo"][key] for key in keys}
    assert cid_system_info == {
        "/Registry": "Adobe",
        "/Ordering": "Identity",
        "/Supplement": 0,
    }
    assert {key: encoding["/CIDSystemInfo"][key] for key in keys} == cid_system_info

    # A CIDFontType0 with a name-keyed CFF program uses CIDs as glyph
    # indices into its CharStrings (ISO 32000-1, 9.7.4.2): follow each
    # character through the ToUnicode CMap (code), the encoding CMap
    # (CID) and the charset of the CFF program (glyph name)
    cff = CFFFontSet()
    cff.decompile(BytesIO(font_file.get_data()), None)
    glyph_names = cff.topDictIndex[0].charset
    code_to_cid = re.findall(
        rb"<([0-9A-F]{4})> (\d+)", _cmap_mappings(font["/Encoding"])
    )
    code_to_char = re.findall(
        rb"<([0-9A-F]{4})> <([0-9A-F]{4})>", _cmap_mappings(font["/ToUnicode"])
    )
    cid_by_code = {int(code, 16): int(cid) for code, cid in code_to_cid}
    shown = {
        chr(int(unicode, 16)): glyph_names[cid_by_code[int(code, 16)]]
        for code, unicode in code_to_char
        if int(code, 16)  # skip .notdef
    }

    # Each character must be shown with its glyph from the original font
    with TTFont(HERE / "Quicksand-Regular.otf") as ttfont:
        cmap = ttfont.getBestCmap()
    assert shown == {char: cmap[ord(char)] for char in set(text)}
