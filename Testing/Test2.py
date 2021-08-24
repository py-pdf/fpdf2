from fpdf import encryption
from fpdf import FPDF
from fpdf.encryption import Encryption, EncryptionInfo, Permissions, Pdf


no_extracting = Permissions(extract=False)

# op = Pdf.open('tuto2.pdf')
# Pdf.save(op, encryption=Encryption(user="123", owner="134", allow=no_extracting))

pdf = Encryption.open('tuto2.pdf')
Encryption.save('output_filename.pdf', encryption=Encryption(owner="123", user="123", allow=no_extracting))
# you can change the R from 4 to 6 for 256 aes encryption
