from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        # Logo
        self.image("../docs/fpdf2-logo.png", 10, 8, 33)
        # helvetica bold 15
        self.set_font("helvetica", "B", 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, "Title", 1, 0, "C")
        # Line break
        self.ln(20)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # helvetica italic 8
        self.set_font("helvetica", "I", 8)
        # Page number
        self.cell(0, 10, "Page " + str(self.page_no()) + "/{nb}", 0, 0, "C")


# Instantiation of inherited class
pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font("Times", size=12)
for i in range(1, 41):
    pdf.cell(0, 10, "Printing line number " + str(i), 0, 1)
pdf.output("tuto2.pdf")
