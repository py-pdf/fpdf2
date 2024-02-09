from mistletoe import markdown

html = markdown(
    """
# Unicode:

| Emoji | Description |
| --- | - |
| 😀 | GRINNING FACE |
| 😁 | GRINNING FACE WITH SMILING EYES |
| 😈 | SMILING FACE WITH HORNS |

# A checklist:

* ☐ item 1
* ☑ item 2
* ☐ item 3
"""
)

from fpdf import FPDF

pdf = FPDF()
pdf.add_font("DejaVuSans", fname="test/fonts/DejaVuSans.ttf")
pdf.add_font("DejaVuSans", fname="test/fonts/DejaVuSans-Bold.ttf", style="B")
pdf.set_font("DejaVuSans", size=24)
pdf.add_page()
pdf.write_html(html)
pdf.output("pdf-from-markdown.pdf")
