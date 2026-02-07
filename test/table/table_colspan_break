from fpdf import FPDF

class TablePDF(FPDF):
    def active_spanning_table(self, data_list, rows_per_page=25):
        self.set_font("helvetica", size=11)
        col_widths = [60, 60, 60]
        self.set_fill_color(200, 200, 200)
        headers = ["Header 1", "Header 2", "Header 3"]
        
        def draw_header():
            for i, header in enumerate(headers):
                self.cell(col_widths[i], 10, header, border=1, fill=True)
            self.ln()
        
        draw_header()
        
        for group in data_list:
            items = group['items']
            label = group['label']
            for chunk_idx in range(0, len(items), rows_per_page):
                chunk = items[chunk_idx:chunk_idx + rows_per_page]
                if self.get_y() > 250:
                    self.add_page()
                    draw_header()
                
                display_label = f"{label}\n" if chunk_idx > 0 else label
                
                y_start = self.get_y()
                self.multi_cell(col_widths[0], 10, display_label, border=1, align='C')
                y_after_label = self.get_y()
                
                self.set_xy(self.l_margin + col_widths[0], y_start)
                self.cell(col_widths[1], 10, "", border=1) 
                self.cell(col_widths[2], 10, chunk[0], border=1)
                self.ln()
                
                for item in chunk[1:]:
                    if self.get_y() > 270: 
                        self.add_page()
                        draw_header()
                        self.multi_cell(col_widths[0], 10, f"{label}\n(suite)", border=1, align='C')
                        self.set_xy(self.l_margin + col_widths[0], self.get_y() - 10)
                    
                    self.set_x(self.l_margin + col_widths[0])
                    self.cell(col_widths[1], 10, "", border=1)  
                    self.cell(col_widths[2], 10, item, border=1)
                    self.ln()

pdf = TablePDF()
pdf.add_page()

data = [
    {"label": "Data 1", "items": [f"Ligne {i}" for i in range(100)]}
]

pdf.active_spanning_table(data, rows_per_page=25)
pdf.output("spantest2.pdf")
