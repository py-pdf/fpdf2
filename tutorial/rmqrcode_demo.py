from fpdf import FPDF
from rmqrcode import QRImage, rMQR

qr = rMQR.fit("https://py-pdf.github.io/fpdf2/")
qrimg = QRImage(qr, module_size=1)

pdf = FPDF()
pdf.add_page()
pdf.image(qrimg._img, w=100, x="CENTER")
pdf.output("rmqrcode.pdf")
