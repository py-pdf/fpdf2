from fpdf import FPDF

pdf = FPDF()

# Add a page
pdf.add_page()

# Set fill color (RGB)
pdf.set_fill_color(255, 205, 0)  # Setting the color to yellow

# Draw the outer rectangle
outer_rect_x, outer_rect_y, outer_rect_w, outer_rect_h = 10, 10, 50, 30
pdf.ellipse(
    outer_rect_x, outer_rect_y, outer_rect_w, outer_rect_h, "F"
)  # Fill the outer rectangle

# Pattern properties
pattern_width, pattern_height = 5, 10  # Width and height of the small rectangles
cols = int(outer_rect_w / pattern_width)  # Number of small rectangles horizontally
rows = int(outer_rect_h / pattern_height)  # Number of small rectangles vertically

# Set color for the pattern
pdf.set_fill_color(255, 255, 255)  # White for the spacing

# Create the pattern
for i in range(cols):
    for j in range(rows):
        if (i + j) % 2 == 0:  # Check for alternate placement
            x = outer_rect_x + i * pattern_width
            y = outer_rect_y + j * pattern_height
            pdf.rect(x, y, pattern_width, pattern_height, "F")

pdf.set_draw_color(0, 0, 0)  # Black border
pdf.ellipse(outer_rect_x, outer_rect_y, outer_rect_w, outer_rect_h)

# Output the PDF
pdf.output("pattern_filled_rectangle.pdf")
