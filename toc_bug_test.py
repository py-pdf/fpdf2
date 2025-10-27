from fpdf import FPDF
from fpdf.outline import TableOfContents

NUMBER_SECTIONS = 100

def p(pdf, text):
    pdf.multi_cell(w=pdf.epw, h=pdf.font_size, text=text, new_x='LMARGIN', new_y='NEXT')

class CustomFPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', size=8)
        text = f'Page {self.page_no()} of {self._total_pages}'
        self.cell(w=0, h=10, text=text, align='C')
        self.set_font('Helvetica', size=12)

def build_pdf(pdf):
    pdf.set_font('Helvetica', size=12)
    pdf.add_page()
    pdf.set_page_label(label_style='R')
    pdf.start_section('Test', level=0)
    pdf.insert_toc_placeholder(TableOfContents().render_toc, allow_extra_pages=True)
    pdf.set_page_label(label_style='D')
    text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 20
    for i in range(1, NUMBER_SECTIONS + 1):
        if i > 1:
            pdf.add_page()
        pdf.start_section(f'Section {i}', level=1)
        p(pdf, f'Section {i}')
        p(pdf, text)

pdf_count = CustomFPDF()
pdf_count._total_pages = 0
pdf_count.set_font('Helvetica', size=12)
build_pdf(pdf_count)
total_pages = pdf_count.page_no()

pdf_final = CustomFPDF()
pdf_final._total_pages = total_pages
build_pdf(pdf_final)
pdf_final.output('output.pdf')
print(f'PDF generated: output.pdf with {total_pages} pages')

