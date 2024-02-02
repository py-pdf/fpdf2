import io
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF

np.random.seed(1)

N = 100
x = np.random.rand(N)
y = np.random.rand(N)
colors = np.random.rand(N)
sz = np.random.rand(N) * 30

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker=go.scatter.Marker(
            size=sz, color=colors, opacity=0.6, colorscale="Viridis"
        ),
    )
)

# Convert the figure to png using kaleido
image_data = fig.to_image(format="png", engine="kaleido")

# Create an io.BytesIO object which can be used by FPDF2
image = io.BytesIO(image_data)
pdf = FPDF()
pdf.add_page()
pdf.image(image, w=pdf.epw)  # Width of the image is equal to the width of the page
pdf.output("plotly_demo.pdf")
