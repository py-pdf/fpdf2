from fpdf import FPDF

pdf = FPDF(orientation='P', unit='mm', format='A4')
pdf.add_page()

# Title
pdf.set_font("Helvetica", 'B', 20)
pdf.set_text_color(0, 102, 204)
pdf.cell(0, 10, "BRAZILIAN SENSI PACK - Itachix.f", ln=True, align='C')

pdf.ln(5)

# Device info
pdf.set_font("Helvetica", '', 14)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 8, "Device: Narzo 70", ln=True)

# Sensitivity
pdf.set_font("Helvetica", 'B', 14)
pdf.cell(0, 8, "Sensitivity Settings:", ln=True)
pdf.set_font("Helvetica", '', 12)
pdf.cell(0, 6, "• General - 153", ln=True)
pdf.cell(0, 6, "• Red Dot - 97", ln=True)
pdf.cell(0, 6, "• 2x Scope - 119", ln=True)
pdf.cell(0, 6, "• 4x Scope - 149", ln=True)
pdf.cell(0, 6, "• 8x Scope - 170", ln=True)
pdf.cell(0, 6, "• F Bot - 196", ln=True)

pdf.ln(3)
pdf.cell(0, 6, "DPI: 360", ln=True)

# Player info
pdf.cell(0, 6, "Player Name: BT GOL7", ln=True)

# Device specs
pdf.cell(0, 6, "Device Info:", ln=True)
pdf.cell(0, 6, "• RAM: 16GB", ln=True)
pdf.cell(0, 6, "• Model: RMX3868", ln=True)
pdf.cell(0, 6, "• Screen: 19.94cm", ln=True)

pdf.ln(2)
pdf.cell(0, 6, "Social Tags: FreefireBrazil, FreefireIndia", ln=True)

# Terms & Policy
pdf.ln(3)
pdf.multi_cell(0, 6, "Terms & Policy:\nThis sensitivity pack is designed for optimal gameplay in Free Fire. Use responsibly and enjoy improved aim and consistency. Sharing without permission is not allowed.")

# Save PDF
pdf.output("Brazilian_Sensi_Pack_Itachixf.pdf")
