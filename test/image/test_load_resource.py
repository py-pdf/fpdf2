"""load_resource.py"""

import unittest
import sys
import os
import fpdf
from io import BytesIO


# python -m unittest test.image.load_resource.LoadResourceTest

from test.utilities import relative_path_to


class LoadResourceTest(unittest.TestCase):
    def test_recognize_bytesIO(self):
        s = BytesIO()
        a = fpdf.image_parsing.load_resource(s)
        self.assertEqual(a, s)

    def test_error_wrong_reason(self):
        with self.assertRaises(Exception) as e:
            fpdf.image_parsing.load_resource(None, reason="not image")

        msg = 'Unknown resource loading reason "not image"'
        self.assertEqual(msg, str(e.exception))

    def test_load_text_file(self):
        file = relative_path_to("__init__.py")
        contents = '"""This package contains image tests"""\n'
        bc = contents.encode("utf-8")

        resource = fpdf.image_parsing.load_resource(file).getvalue()
        self.assertEqual(bytes(resource), bc)
        # print(bytes(resource))
        # print(bc)
