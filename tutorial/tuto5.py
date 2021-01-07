from fpdf import *


class PDF(FPDF):
    # Load data
    def load_data(self, name):
        # Read file lines
        data = []
        with open(name) as file:
            for line in file:
                data += [line[:-1].split(";")]
        return data

    # Simple table
    def basic_table(self, header, data):
        # Header
        for col in header:
            self.cell(40, 7, col, 1)
        self.ln()
        # Data
        for row in data:
            for col in row:
                self.cell(40, 6, col, 1)
            self.ln()

    # Better table
    def improved_table(self, header, data):
        # Column widths
        w = [40, 35, 40, 45]
        # Header
        for i in range(0, len(header)):
            self.cell(w[i], 7, header[i], 1, 0, "C")
        self.ln()
        # Data
        for row in data:
            self.cell(w[0], 6, row[0], "LR")
            self.cell(w[1], 6, row[1], "LR")
            self.cell(w[2], 6, row[2], "LR", 0, "R")
            self.cell(w[3], 6, row[3], "LR", 0, "R")
            self.ln()
        # Closure line
        self.cell(sum(w), 0, "", "T")

    # Colored table
    def fancy_table(self, header, data):
        # Colors, line width and bold font
        self.set_fill_color(255, 0, 0)
        self.set_text_color(255)
        self.set_draw_color(128, 0, 0)
        self.set_line_width(0.3)
        self.set_font("", "B")
        # Header
        w = [40, 35, 40, 45]
        for i in range(0, len(header)):
            self.cell(w[i], 7, header[i], 1, 0, "C", 1)
        self.ln()
        # Color and font restoration
        self.set_fill_color(224, 235, 255)
        self.set_text_color(0)
        self.set_font("")
        # Data
        fill = 0
        for row in data:
            self.cell(w[0], 6, row[0], "LR", 0, "L", fill)
            self.cell(w[1], 6, row[1], "LR", 0, "L", fill)
            self.cell(w[2], 6, row[2], "LR", 0, "R", fill)
            self.cell(w[3], 6, row[3], "LR", 0, "R", fill)
            self.ln()
            fill = not fill
        self.cell(sum(w), 0, "", "T")


pdf = PDF()
# Column titles
header = ["Country", "Capital", "Area (sq km)", "Pop. (thousands)"]
# Data loading
data = pdf.load_data("countries.txt")
pdf.set_font("Arial", "", 14)
pdf.add_page()
pdf.basic_table(header, data)
pdf.add_page()
pdf.improved_table(header, data)
pdf.add_page()
pdf.fancy_table(header, data)
pdf.output("tuto5.pdf", "F")
