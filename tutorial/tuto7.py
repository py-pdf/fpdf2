from fpdf import *

pdf = FPDF()
pdf.add_font("Calligrapher", "", "calligra")
pdf.add_page()
pdf.set_font("Calligrapher", "", 35)
pdf.cell(0, 10, "Enjoy new fonts with FPDF!")
pdf.output("tuto7.pdf")
