from fpdf import FPDF
from pathlib import Path
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

def test_table_colspan_break(tmp_path):

    def active_spanning_table(pdf, data_list, rows_per_page=25):
        pdf.set_font("helvetica", size=11)
        col_widths = [60, 60, 60]
        pdf.set_fill_color(200, 200, 200)
        headers = ["Header 1", "Header 2", "Header 3"]
        
        def draw_header():
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, border=1, fill=True)
            pdf.ln()
        
        draw_header()
        
        for group in data_list:
            items = group['items']
            label = group['label']
            for chunk_idx in range(0, len(items), rows_per_page):
                chunk = items[chunk_idx:chunk_idx + rows_per_page]
                if pdf.get_y() > 250:
                    pdf.add_page()
                    draw_header()
                
                display_label = f"{label}\n" if chunk_idx > 0 else label
                
                y_start = pdf.get_y()
                pdf.multi_cell(col_widths[0], 10, display_label, border=1, align='C')
                y_after_label = pdf.get_y()
                
                pdf.set_xy(pdf.l_margin + col_widths[0], y_start)
                pdf.cell(col_widths[1], 10, "", border=1) 
                pdf.cell(col_widths[2], 10, chunk[0], border=1)
                pdf.ln()
                
                for item in chunk[1:]:
                    if pdf.get_y() > 270: 
                        pdf.add_page()
                        draw_header()
                        pdf.multi_cell(col_widths[0], 10, f"{label}\n(suite)", border=1, align='C')
                        pdf.set_xy(pdf.l_margin + col_widths[0], pdf.get_y() - 10)
                    
                    pdf.set_x(pdf.l_margin + col_widths[0])
                    pdf.cell(col_widths[1], 10, "", border=1)  
                    pdf.cell(col_widths[2], 10, item, border=1)
                    pdf.ln()

    pdf = FPDF()
    pdf.add_page()

    data = [
        {"label": "Data 1", "items": [f"Ligne {i}" for i in range(100)]}
    ]

    active_spanning_table(pdf, data, rows_per_page=25)

    assert_pdf_equal(pdf, HERE / "table_colspan_break.pdf", tmp_path)
