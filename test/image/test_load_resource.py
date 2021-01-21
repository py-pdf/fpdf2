"""load_resource.py"""

from io import BytesIO

import pytest

import fpdf
from fpdf.errors import FPDFException

from test.utilities import relative_path_to


class TestLoadResource:
    def test_recognize_bytesIO(self):
        s = BytesIO()
        a = fpdf.image_parsing.load_resource(s)
        assert a == s

    def test_error_wrong_reason(self):
        with pytest.raises(FPDFException) as e:
            fpdf.image_parsing.load_resource(None, reason="not image")

        msg = 'Unknown resource loading reason "not image"'
        assert msg == str(e.value)

    def test_load_text_file(self):
        file = relative_path_to("__init__.py")
        contents = '"""This package contains image tests"""\n'
        bc = contents.encode("utf-8")

        resource = fpdf.image_parsing.load_resource(file).getvalue()
        assert bytes(resource) == bc
        # print(bytes(resource))
        # print(bc)
