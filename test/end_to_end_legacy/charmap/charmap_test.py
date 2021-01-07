"""Charmap Test Case

This module contains the test case for the Charmap Test. It prints the first
999 characters of the unicode character set with a unicode ttf font, and
verifies the result against a known good result.

This test will complain that some of the values in this font file are out of
the range of the C 'short' data type (2 bytes, 0 - 65535):
  fpdf/ttfonts.py:671: UserWarning: cmap value too big/small:
and this seems to be okay.
"""
import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..", "..")
    ),
)

import fpdf
from fpdf.ttfonts import TTFontFile
from test.utilities import relative_path_to, calculate_hash_of_file, set_doc_date_0

# python -m unittest test.end_to_end_legacy.charmap.charmap_test.CharmapTest


class MyTTFontFile(TTFontFile):
    """MyTTFontFile docstring

    I clearly have no idea what this does. It'd be great if this class were
    even a little bit better documented, so that it would be clearer what this
    test is testing, otherwise this test isn't clearly testing one class or the
    other.

    """

    def getCMAP4(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        TTFontFile.getCMAP4(self, unicode_cmap_offset, glyphToChar, charToGlyph)
        self.saveChar = charToGlyph

    def getCMAP12(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        TTFontFile.getCMAP12(self, unicode_cmap_offset, glyphToChar, charToGlyph)
        self.saveChar = charToGlyph


class CharmapTest(unittest.TestCase):
    def test_first_999_chars(self):
        for fontpath, known_output_hash in (
            ("DejaVuSans.ttf", "22069d93f0f6cef7f5da8f828c9f067c"),
            ("DroidSansFallback.ttf", "ef03734fa0c3ed09d9260ec1ed3c5dce"),
            ("Roboto-Regular.ttf", "5c5f18aaf8afac13261b277b1c9bd9cf"),
            ("cmss12.ttf", "7cc4db652e8ad297be9413926b832707"),
        ):
            with self.subTest(fontpath=fontpath):
                fontname = os.path.splitext(fontpath)[0]
                fontpath = relative_path_to(fontpath)

                pdf = fpdf.FPDF()
                pdf.add_page()
                pdf.add_font(fontname, "", fontpath, uni=True)
                pdf.set_font(fontname, "", 10)

                ttf = MyTTFontFile()
                ttf.getMetrics(fontpath)

                # Create a PDF with the first 999 charters defined in the font:
                for counter, character in enumerate(ttf.saveChar, 0):
                    pdf.write(8, u"%03d) %03x - %c" % (counter, character, character))
                    pdf.ln()
                    if counter >= 999:
                        break

                testing_output = relative_path_to("charmap_test_output.pdf")
                set_doc_date_0(pdf)
                pdf.output(testing_output)

                output_hash = calculate_hash_of_file(testing_output)
                self.assertEqual(known_output_hash, output_hash)
                os.unlink(testing_output)

                # clear out all the pkl files
                pklList = [f for f in relative_path_to(".") if f.endswith(".pkl")]
                for f in pklList:
                    os.remove(relative_path_to(f))


if __name__ == "__main__":
    unittest.main()

## Code used to create test:
# fontpath = relative_path_to('DejaVuSans.ttf')

# pdf = fpdf.FPDF()
# pdf.compression = True
# pdf.add_page()
# pdf.add_font('font', '', fontpath, uni = True)
# pdf.set_font('font', '', 10)

# ttf = MyTTFontFile()
# ttf.getMetrics(fontpath)

# for counter, character in enumerate(ttf.saveChar, 0):
#   # print (counter, character)
#   pdf.write(8, u"%03d) %06x - %c" % (counter, character, character))
#   pdf.ln()

#   if counter >= 999: break

# output = relative_path_to('charmap_test_output.pdf')

# set_doc_date_0(pdf)
# pdf.output(output)
# print calculate_hash_of_file(output)
# os.unlink(output)
