import unittest

from fpdf.ttfonts import str_pad
from fpdf.util import UTF8ToUTF16BE

# python -m unittest test.utils.text_utils.UtilsTest


class UtilsTest(unittest.TestCase):
    def test_UTF8ToUTF16BE(self):
        self.assertIsNotNone(UTF8ToUTF16BE("abc", False))

    def test_str_pad(self):
        self.assertEqual(str_pad("ok", 20), "ok                  ")
        self.assertEqual(str_pad("ok", 20, "+"), "ok++++++++++++++++++")
        self.assertEqual(str_pad("ok", 20, "-", 0), "---------ok---------")
        self.assertEqual(str_pad("ok", 20, "-", 1), "ok------------------")
        self.assertEqual(str_pad("ok", 20, "-", -1), "------------------ok")
