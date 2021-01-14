import unittest

from fpdf.template import Template

from test.utilities import assert_pdf_equal, relative_path_to

# python -m unittest test.template.test_template


class TemplateTest(unittest.TestCase):
    def test_nominal_hardcoded(self):
        "Taken from docs/Templates.md"
        elements = [
            {
                "name": "company_logo",
                "type": "I",
                "x1": 20.0,
                "y1": 17.0,
                "x2": 78.0,
                "y2": 30.0,
                "font": None,
                "size": 0.0,
                "bold": 0,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": "logo",
                "priority": 2,
            },
            {
                "name": "company_name",
                "type": "T",
                "x1": 17.0,
                "y1": 32.5,
                "x2": 115.0,
                "y2": 37.5,
                "font": "helvetica",
                "size": 12.0,
                "bold": 1,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": "",
                "priority": 2,
            },
            {
                "name": "box",
                "type": "B",
                "x1": 15.0,
                "y1": 15.0,
                "x2": 185.0,
                "y2": 260.0,
                "font": "helvetica",
                "size": 0.0,
                "bold": 0,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": None,
                "priority": 0,
            },
            {
                "name": "box_x",
                "type": "B",
                "x1": 95.0,
                "y1": 15.0,
                "x2": 105.0,
                "y2": 25.0,
                "font": "helvetica",
                "size": 0.0,
                "bold": 1,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": None,
                "priority": 2,
            },
            {
                "name": "line1",
                "type": "L",
                "x1": 100.0,
                "y1": 25.0,
                "x2": 100.0,
                "y2": 57.0,
                "font": "helvetica",
                "size": 0,
                "bold": 0,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": None,
                "priority": 3,
            },
            {
                "name": "barcode",
                "type": "BC",
                "x1": 20.0,
                "y1": 246.5,
                "x2": 140.0,
                "y2": 254.0,
                "font": "Interleaved 2of5 NT",
                "size": 0.75,
                "bold": 0,
                "italic": 0,
                "underline": 0,
                "foreground": 0,
                "background": 0,
                "align": "I",
                "text": "200000000001000159053338016581200810081",
                "priority": 3,
            },
        ]
        tmpl = Template(format="A4", elements=elements, title="Sample Invoice")
        tmpl.add_page()
        tmpl["company_name"] = "Sample Company"
        tmpl["company_logo"] = relative_path_to("../../docs/fpdf2-logo.png")
        assert_pdf_equal(self, tmpl, "test_nominal_hardcoded.pdf")

    def test_nominal_csv(self):
        "Taken from docs/Templates.md"
        tmpl = Template(format="A4", title="Sample Invoice")
        tmpl.parse_csv(relative_path_to("mycsvfile.csv"), delimiter=";")
        tmpl.add_page()
        tmpl["company_name"] = "Sample Company"
        assert_pdf_equal(self, tmpl, "test_nominal_csv.pdf")
