

import  fpdf

fix = True

def stamp(pdf, x, y):
    pdf.set_text_color(0x0)
    pdf.set_fill_color(0xFFFFFF)
    pdf.set_draw_color(0x0)
    pdf.set_line_width(0)

    pdf.set_font("times", "", 20)

    pdf.rect(0+x,  0+y, 50, 50, style="FD")
    pdf.line(0+x,  0+y, 50+x, 50+y)
    pdf.line(0+x, 50+y, 50+x,  0+y)
    pdf.set_xy(0+x, 52+y)
    pdf.cell(50,5,"this is a label", border=0, ln=0, align="L", fill=True)

pdf = fpdf.FPDF()
pdf.add_page()

if fix:
    pdf.set_font("helvetica", "", 10)

for r,x,y in ((5, 50,50),(10,50,120), (15,120,50),(20,120,120)):
    with pdf.rotation(r, x, y):
        stamp(pdf, x,y)

pdf.output("badrot.pdf")
