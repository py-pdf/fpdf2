from fpdf import FPDF
from fpdf.enums import TableSpan

pdf = FPDF()

pdf.auto_page_break = True
pdf.set_font("Arial", size=12)
pdf.add_page()

data = [
    ["Header 1", "Header 2", "Header 3"],
    ["Data 1", "Data 2", "Data 3"],
] + [[TableSpan.ROW, "Data 5", "Data 6"]] * 30 #this seems to be the threshold -> 32 rows of this size

with pdf.table(data) as table:
    pass

pdf.output("overly_long_tablespan.pdf")
print("Wrote overly_long_tablespan.pdf")
