from io import BytesIO
from fpdf import FPDF
from barcode import Code128
from barcode.writer import SVGWriter

# Create a new PDF document
pdf = FPDF()
pdf.add_page()

# Set the position and size of the image in the PDF
x = 50
y = 50
w = 100
h = 70

# Generate a Code128 Barcode as SVG:
svg_img_bytes = BytesIO()
Code128("100000902922", writer=SVGWriter()).write(svg_img_bytes)
pdf.image(svg_img_bytes, x=x, y=y, w=w, h=h)

# Output a PDF file:
pdf.output("code128_barcode.pdf")
