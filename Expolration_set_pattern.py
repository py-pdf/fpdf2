from fpdf import FPDF

# Create instance of FPDF class
pdf = FPDF()

# Add a page
r= pdf.add_page()

# Set fill color (RGB)
pdf.set_fill_color(255, 205, 0)  # Setting the color to red

#pdf.set_page_background('/Users/lamamasri/Desktop/image_13.gif')
w1=10
w2=10
w3=50
w4=40
pdf.rect(10,10,50,30)

n=0
while n<=50:
    

    pdf.rect(w1, w2,w3/10, w3/10, 'F')
    pdf.rect(w1, w2+10,w3/10, w3/10, 'F')
    pdf.rect(w1, w2+20,w3/10, w3/10, 'F')
    pdf.rect(w1, w2+28,w3/10, w3/10, 'F')
    w1=w1+w3/5
    
    n=n+10
    print("N1: ",n)
    print("W1; ,", w1)

# Draw a filled rectangle
#for i in range (w3):
    #pdf.rect(w1, w2,w3/10, w3/10, 'F')
    
#pdf.rect(10, 10, 5, 5, 'F')  # 'F' argument is for fill

#pdf.rect(20, 10, 5, 5, 'F')

#pdf.rect(30, 10, 5, 5, 'F')




# Output the PDF
pdf.output('filled_rectangle.pdf')