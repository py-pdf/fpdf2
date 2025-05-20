from fpdf import FPDF
from aztec_code_generator import AztecCode


pdf = FPDF()
pdf.add_page()
aztec_code = AztecCode("https://py-pdf.github.io/fpdf2/")
pdf.image(aztec_code.image(), x=10, y=10, w=100, h=100)
pdf.output("aztec_code.pdf")
