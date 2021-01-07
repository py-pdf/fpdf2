from FPDF.Bookmark import *

pdf = Bookmark()
pdf.Open()
pdf.SetFont("Arial", "", 15)
# Page 1
pdf.AddPage()
pdf.Bookmark("Page 1")
pdf.Bookmark("Paragraph 1", 1, -1)
pdf.Cell(0, 6, "Paragraph 1")
pdf.Ln(50)
pdf.Bookmark("Paragraph 2", 1, -1)
pdf.Cell(0, 6, "Paragraph 2")
# Page 2
pdf.AddPage()
pdf.Bookmark("Page 2")
pdf.Bookmark("Paragraph 3", 1, -1)
pdf.Cell(0, 6, "Paragraph 3")
pdf.Output("bookmark.pdf", "F")
