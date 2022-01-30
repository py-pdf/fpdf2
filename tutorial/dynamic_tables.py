from fpdf import FPDF

def number_generator(number, until, increaser):
    """Generate numbers for making tables dynamic"""
    result = []
    while number < until:
        result.append(number)
        number += increaser
    return result

class PDF(FPDF):
    def header(self):
        self.image('../docs/fpdf2-logo.png', 160, 8, 33)
        self.set_font('helvetica', '', 10)
        self.cell(40, 10, 'Receipt', 0, 1, 'L')
        self.set_font('helvetica', 'B', 15)
        self.cell(20, 10, 'Retro Restaurant', 0, 0, 'L')
        self.ln(10)

def generate_PDF(data):
    """Generate PDF file"""

    # Setup PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font('Times', '', 12)
    txid = 'Transaction for table Number: 45'
    tx_time_stamp = 'Transaction time: Sunday, 30 Jan 2022 15:34:23 PM'
    tx_status = 'Paid by Nima.'

    pdf.ln()
    pdf.ln()

    pdf.multi_cell(0, 5, txid)
    pdf.ln()

    pdf.multi_cell(0, 5, tx_time_stamp)
    pdf.ln()

    pdf.multi_cell(0, 5, tx_status)
    pdf.ln()

    pdf.set_font('Times', '', 15)
    pdf.cell(0, 10, 'Foods:', 0, 1)

    row_names = [
        ['#','Food name','Value (USD)','Status'],
        ]



    for i in range(0, data['number_of_foods']):
        row_names.append([
            str(i),
            data['Foods']['Food_name'][i],
            data['Foods']['Food_price'][i],
            data['Foods']['Status'][i],
        ])

    pdf.set_font('Times','',10.0)
    pdf.ln(0.5)
    
    th = pdf.font_size

    pdf.set_font('Times','',10.0)
    pdf.ln(0.5)

    iterator_number = 0
    for row in row_names:
        for datum in row:
            # we use 4 as increaser because our data has 4 column
            # if results are more than 30, increase the number
            if (iterator_number in number_generator(0, 30, 4)):
                pdf.cell(10, 2*th, str(datum), align = 'C', border=1)
            elif (iterator_number in number_generator(1, 30, 4)):
                pdf.cell(110, 2*th, str(datum), align = 'C', border=1)
            elif (iterator_number in number_generator(2, 30, 4)):
                pdf.cell(30, 2*th, str(datum), align = 'C', border=1)
            elif (iterator_number in number_generator(3, 30, 4)):
                pdf.cell(30, 2*th, str(datum), align = 'C', border=1)
            iterator_number += 1
        pdf.ln(2*th)
    
    pdf.cell(180, 2*th, 'Total: ' + '$' + str(data['input_total_value_usd']), align = 'L', border=1)

    pdf.ln()
    pdf.ln()

    pdf.output('dynamic_tables.pdf', 'F')


data = {
'number_of_foods': 3,
'input_total_value_usd': 13,
'Foods': 
{'Food_name': ['Salad', 'Soda', 'Kebab'],
'Food_price': [2, 1, 10],
'Status': ['Paid', 'Paid', 'Paid', ]
}}

generate_PDF(data)