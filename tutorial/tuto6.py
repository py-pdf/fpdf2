from fpdf import *
import re


class PDF(FPDF):
    def __init__(self, orientation="P", unit="mm", format="A4"):
        # Call parent constructor
        FPDF.__init__(self, orientation, unit, format)
        # Initialization
        self.b = 0
        self.i = 0
        self.href = ""
        self.page_links = {}

    def write_html(self, html):
        # HTML parser
        html = html.replace("\n", " ")
        a = re.split("<(.*?)>", html)
        for i, e in enumerate(a):
            if i % 2 == 0:
                # Text
                if self.href:
                    self.put_link(self.href, e)
                else:
                    self.write(5, e)
            else:
                # Tag
                if e[0] == "/":
                    self.close_tag(e[1:].upper())
                else:
                    # Extract attributes
                    attr = {}
                    a2 = e.split(" ")
                    tag = a2.pop(0).upper()
                    for v in a2:
                        a3 = re.findall("""^([^=]*)=["']?([^"']*)["']?""", v)[0]
                        if a3:
                            attr[a3[0].upper()] = a3[1]
                    self.open_tag(tag, attr)

    def open_tag(self, tag, attr):
        # Opening tag
        if tag in ("B", "I", "U"):
            self.set_style(tag, 1)
        if tag == "A":
            self.href = attr["HREF"]
        if tag == "BR":
            self.ln(5)

    def close_tag(self, tag):
        # Closing tag
        if tag in ("B", "I", "U"):
            self.set_style(tag, 0)
        if tag == "A":
            self.href = ""

    def set_style(self, tag, enable):
        # Modify style and select corresponding font
        t = getattr(self, tag.lower())
        if enable:
            t += 1
        else:
            t += -1
        setattr(self, tag.lower(), t)
        style = ""
        for s in ("B", "I", "U"):
            if getattr(self, s.lower()) > 0:
                style += s
        self.set_font("", style)

    def put_link(self, url, txt):
        # Put a hyperlink
        self.set_text_color(0, 0, 255)
        self.set_style("U", 1)
        self.write(5, txt, url)
        self.set_style("U", 0)
        self.set_text_color(0)


html = """You can now easily print text mixing different
styles: <B>bold</B>, <I>italic</I>, <U>underlined</U>, or
<B><I><U>all at once</U></I></B>!<BR>You can also insert links
on text, such as <A HREF="http://www.fpdf.org">www.fpdf.org</A>,
or on an image: click on the logo."""

pdf = PDF()
# First page
pdf.add_page()
pdf.set_font("Arial", "", 20)
pdf.write(5, "To find out what's new in self tutorial, click ")
pdf.set_font("", "U")
link = pdf.add_link()
pdf.write(5, "here", link)
pdf.set_font("")
# Second page
pdf.add_page()
pdf.set_link(link)
pdf.image("logo.png", 10, 10, 30, 0, "", "http://www.fpdf.org")
pdf.set_left_margin(45)
pdf.set_font_size(14)
pdf.write_html(html)
pdf.output("tuto6.pdf", "F")
