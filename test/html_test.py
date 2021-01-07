import fpdf
import os
import unittest
from fpdf.html import px2mm
from test.utilities import assert_pdf_equal

# python -m unittest test.html_test.HTMLTest
# python -m unittest test.html_test.HTMLAllFeaturesTest


class MyFPDF(fpdf.FPDF, fpdf.HTMLMixin):
    pass


class HTMLTest(unittest.TestCase):
    "This test executes some possible inputs to FPDF#HTMLMixin."

    def test_html_images(self):
        pdf = MyFPDF()
        pdf.add_page()
        rel = os.path.dirname(os.path.abspath(__file__))
        img_path = rel + "/image/png_images/c636287a4d7cb1a36362f7f236564cef.png"

        initial = 10
        mm_after_image = initial + px2mm(300)
        self.assertEqual(round(pdf.get_x()), 10, "Initial x margin is not expected")
        self.assertEqual(round(pdf.get_y()), 10, "Initial y margin is not expected")
        self.assertEqual(round(pdf.w), 210, "Page width is not expected")
        pdf.write_html(
            "<center><img src=\"%s\" height='300' width='300'></center>" % img_path
        )
        # Unable to text position of the image as write html moves to a new line after
        # adding the image but it can be seen in the produce test.pdf file.
        self.assertEqual(
            round(pdf.get_x()), 10, "Have not moved to beginning of new line"
        )
        self.assertAlmostEqual(
            pdf.get_y(),
            mm_after_image,
            places=2,
            msg="Image height has moved down the page",
        )

        assert_pdf_equal(self, pdf, "test_html_images.pdf")


class HTMLAllFeaturesTest(unittest.TestCase):
    "Try to reach all branches in single document"

    def test_html_features(self):
        pdf = MyFPDF()
        pdf.add_page()
        pdf.write_html("<p><b>hello</b> world. i am <i>tired</i>.</p>")
        pdf.write_html("<p><u><b>hello</b> world. i am <i>tired</i>.</u></p>")
        pdf.write_html(
            "<p><u><strong>hello</strong> world. i am <em>tired</em>.</u></p>"
        )
        pdf.write_html('<p><a href="https://github.com">github</a></p>')
        pdf.write_html('<p align="right">right aligned text</p>')
        pdf.write_html("<p>i am a paragraph <br />in two parts.</p>")
        pdf.write_html('<font color="#00ff00"><p>hello in green</p></font>')
        pdf.write_html('<font size="7"><p>hello small</p></font>')
        pdf.write_html('<font face="helvetica"><p>hello helvetica</p></font>')
        pdf.write_html('<font face="times"><p>hello times</p></font>')
        pdf.write_html("<h1>h1</h1>")
        pdf.write_html("<h2>h2</h2>")
        pdf.write_html("<h3>h3</h3>")
        pdf.write_html("<h4>h4</h4>")
        pdf.write_html("<h5>h5</h5>")
        pdf.write_html("<h6>h6</h6>")
        pdf.write_html("<br />")
        pdf.write_html("<hr />")
        pdf.write_html("<br />")
        pdf.write_html("<br />")
        pdf.write_html("<pre>i am preformatted text.</pre>")
        pdf.write_html("<blockquote>hello blockquote</blockquote>")
        pdf.write_html("<ul><li>li1</li><li>another</li><li>l item</li></ul>")
        pdf.write_html("<ol><li>li1</li><li>another</li><li>l item</li></ol>")
        pdf.write_html('<table width="50"></table>')
        pdf.write_html("<img></img>")
        pdf.write_html(
            "<table>"
            "  <thead>"
            "    <tr>"
            '      <th  width="30%">ID</th>'
            '      <th  width="70%">Name</th>'
            "    </tr>"
            "  </thead>"
            "  <tbody>"
            "    <tr>"
            "      <td>1</td>"
            "      <td>Alice</td>"
            "    <tr>"
            "    <tr>"
            "      <td>2</td>"
            "      <td>Bob</td>"
            "    </tr>"
            "  </tbody>"
            "  <tfoot>"
            "    <tr>"
            '      <td width="50%">id</td>'
            '      <td width="50%">name</td>'
            "    </tr>"
            "  </tfoot>"
            "</table>"
        )
        pdf.write_html('<table width="50"></table>')
        pdf.write_html(
            '<table width="50%">'
            "  <thead>"
            "    <tr>"
            '      <th  width="30%">ID</th>'
            '      <th  width="70%">Name</th>'
            "    </tr>"
            "  </thead>"
            "  <tbody>"
            "    <tr>"
            "      <td>1</td>"
            "      <td>Alice</td>"
            "    <tr>"
            "    <tr>"
            "      <td>2</td>"
            "      <td>Bob</td>"
            "    </tr>"
            "  </tbody>"
            "  <tfoot>"
            "    <tr>"
            '      <td width="50%">id</td>'
            '      <td width="50%">name</td>'
            "    </tr>"
            "  </tfoot>"
            "</table>"
        )

        name = [
            "Alice",
            "Carol",
            "Chuck",
            "Craig",
            "Dan",
            "Erin",
            "Eve",
            "Faythe",
            "Frank",
            "Grace",
            "Heidi",
            "Ivan",
            "Judy",
            "Mallory",
            "Michael",
            "Niaj",
            "Olivia",
            "Oscar",
            "Peggy",
            "Rupert",
            "Sybil",
            "Trent",
            "Trudy",
            "Victor",
            "Walter",
            "Wendy",
        ]

        def getrow(i):
            return "<tr><td>" + str(i) + "</td><td>" + name[i] + "</td></tr>"

        pdf.write_html(
            (
                '<table width="50%">'
                "  <thead>"
                "    <tr>"
                '      <th  width="30%">ID</th>'
                '      <th  width="70%">Name</th>'
                "    </tr>"
                "  </thead>"
                "  <tbody>"
                "    <tr>"
                '      <td colspan="2">Alice</td>'
                "    </tr>"
            )
            + "".join([getrow(i) for i in range(26)])
            + ("  </tbody>" "</table>")
        )

        rel = os.path.dirname(os.path.abspath(__file__))
        img_path = rel + "/image/png_images/c636287a4d7cb1a36362f7f236564cef.png"
        pdf.add_page()
        pdf.write_html("<img src=\"%s\" height='300' width='300'>" % img_path)

        assert_pdf_equal(self, pdf, "test_html_features.pdf")


if __name__ == "__main__":
    unittest.main()
