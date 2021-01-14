import fpdf


class MyFPDF(fpdf.FPDF, fpdf.HTMLMixin):
    pass


pdf = MyFPDF()
# First page
pdf.add_page()
pdf.set_font("helvetica", size=20)
pdf.write(5, "To find out what's new in self tutorial, click ")
pdf.set_font(style="U")
link = pdf.add_link()
pdf.write(5, "here", link)
pdf.set_font()
# Second page
pdf.add_page()
pdf.set_link(link)
pdf.image("../docs/fpdf2-logo.png", 10, 10, 30, 0, "", "http://www.fpdf.org")
pdf.set_left_margin(45)
pdf.set_font_size(14)
pdf.write_html(
    """You can now easily print text mixing different
styles: <B>bold</B>, <I>italic</I>, <U>underlined</U>, or
<B><I><U>all at once</U></I></B>!<BR>You can also insert links
on text, such as <A HREF="http://www.fpdf.org">www.fpdf.org</A>,
or on an image: click on the logo."""
)
pdf.output("tuto6.pdf")
