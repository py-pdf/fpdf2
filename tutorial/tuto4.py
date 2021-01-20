from fpdf import FPDF


class PDF(FPDF):
    # Current column
    col = 0
    # Ordinate of column start
    y0 = 0

    def header(self):
        # Page header
        self.set_font("helvetica", "B", 15)
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        self.set_line_width(1)
        self.cell(w, 9, title, 1, 1, "C", True)
        self.ln(10)
        # Save ordinate
        self.y0 = self.get_y()

    def footer(self):
        # Page footer
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def set_col(self, col):
        # Set position at a given column
        self.col = col
        x = 10 + col * 65
        self.set_left_margin(x)
        self.set_x(x)

    def accept_page_break(self):
        # Method accepting or not automatic page break
        if self.col < 2:
            # Go to next column
            self.set_col(self.col + 1)
            # Set ordinate to top
            self.set_y(self.y0)
            # Keep on page
            return 0

        # Go back to first column
        self.set_col(0)
        # Page break
        return 1

    def chapter_title(self, num, label):
        # Title
        self.set_font("helvetica", "", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f"Chapter {num} : {label}", 0, 1, "L", True)
        self.ln(4)
        # Save ordinate
        self.y0 = self.get_y()

    def chapter_body(self, name):
        # Read text file
        with open(name, "rb") as fh:
            txt = fh.read().decode("latin-1")
        # Font
        self.set_font("Times", size=12)
        # Output text in a 6 cm width column
        self.multi_cell(60, 5, txt)
        self.ln()
        # Mention
        self.set_font(style="I")
        self.cell(0, 5, "(end of excerpt)")
        # Go back to first column
        self.set_col(0)

    def print_chapter(self, num, title, name):
        # Add chapter
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)


pdf = PDF()
title = "20000 Leagues Under the Seas"
pdf.set_title(title)
pdf.set_author("Jules Verne")
pdf.print_chapter(1, "A RUNAWAY REEF", "20k_c1.txt")
pdf.print_chapter(2, "THE PROS AND CONS", "20k_c1.txt")
pdf.output("tuto4.pdf")
