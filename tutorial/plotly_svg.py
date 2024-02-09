from fpdf import FPDF
import plotly.express as px

fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])
fig.write_image("figure.svg")

pdf = FPDF()
pdf.add_page()
pdf.image("figure.svg", w=pdf.epw)
pdf.output("plotly.pdf")
