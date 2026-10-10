from pathlib import Path
from tempfile import TemporaryDirectory

from fpdf import FPDF
from rmqrcode import QRImage, rMQR

qr = rMQR.fit("https://py-pdf.github.io/fpdf2/")
qrimg = QRImage(qr, module_size=1)

pdf = FPDF()
pdf.add_page()

with TemporaryDirectory() as tmpdir:
    image_path = Path(tmpdir) / "rmqrcode.png"
    qrimg.save(image_path)
    pdf.image(image_path, w=100, x="CENTER")

pdf.output("rmqrcode.pdf")
