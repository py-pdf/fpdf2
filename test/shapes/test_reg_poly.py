import sys
sys.path.insert(0, '/Users/londonbettman/Desktop/School/ComputerScience/Software Lab/Git Contribution Project/fpdf2')
from fpdf import FPDF


pdf = FPDF()
pdf.add_page()

#no fill with line
pdf.reg_poly(10,35,3,25)
pdf.reg_poly(50,35,4,25)
pdf.reg_poly(90,35,5,25)
pdf.reg_poly(120,35,6,25)
pdf.reg_poly(150,35,7,25)
pdf.reg_poly(180,35,8,25)

#fill and color test
pdf.set_fill_color(134, 200, 15)
pdf.reg_poly(10,85,3,25, style="f")
pdf.reg_poly(50,85,4,25, style="f")
pdf.reg_poly(90,85,5,25, style="f")
pdf.reg_poly(120,85,6,25, style="f")
pdf.reg_poly(150,85,7,25, style="f")
pdf.reg_poly(180,85,8,25, style="f")

#draw color test
pdf.set_fill_color(0, 0, 0)
pdf.set_draw_color(204, 0, 204)
pdf.reg_poly(10,135,3,25)
pdf.reg_poly(50,136,4,25)
pdf.reg_poly(90,135,5,25)
pdf.reg_poly(120,135,6,25)
pdf.reg_poly(150,135,7,25)
pdf.reg_poly(180,135,8,25)

#line width test
pdf.set_line_width(1)
pdf.reg_poly(10,185,3,25)
pdf.reg_poly(50,186,4,25)
pdf.reg_poly(90,185,5,25)
pdf.reg_poly(120,185,6,25)
pdf.reg_poly(150,185,7,25)
pdf.reg_poly(180,185,8,25)

#line color and fill color
pdf.set_fill_color(3, 190, 252)
pdf.reg_poly(10,235,3,25, style="f")
pdf.reg_poly(50,236,4,25, style="f")
pdf.reg_poly(90,235,5,25, style="f")
pdf.reg_poly(120,235,6,25, style="f")
pdf.reg_poly(150,235,7,25, style="f")
pdf.reg_poly(180,235,8,25, style="f")

#rotation test
pdf.reg_poly(10,285,3,25,30)
pdf.reg_poly(50,285,4,25,45)
pdf.reg_poly(90,285,5,25,200)
pdf.reg_poly(120,285,6,25,0)
pdf.reg_poly(150,285,7,25,13)
pdf.reg_poly(180,285,8,25,22.5)

pdf.output("test_reg_poly.pdf")


#order of draw operations
#text
#scale
#rotate
#translate

#create a thing to take svg/pdf file from