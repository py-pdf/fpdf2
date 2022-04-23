# Usage in web APIs #

## Django ##
[Django](https://www.djangoproject.com/) is:
> a high-level Python web framework that encourages rapid development and clean, pragmatic design

There is how you can return a PDF document from a [Django view](https://docs.djangoproject.com/en/4.0/topics/http/views/):

```python
from django.http import HttpResponse
from fpdf import FPDF

def report(request):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.cell(txt="hello world")
    return HttpResponse(bytes(pdf.output()), content_type='application/pdf')
```

## Flask ##
[Flask](https://flask.palletsprojects.com) is a micro web framework written in Python.

The following code can be placed in a `app.py` file and launched using `flask run`:

```python
from flask import Flask, make_response
from fpdf import FPDF

app = Flask(__name__)

@app.route("/")
def hello_world():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.cell(txt="hello world")
    response = make_response(pdf.output())
    response.headers['Content-Type'] = "application/pdf"
    return response
```

## streamlit ##
[streamlit](https://streamlit.io) is:
> a Python library that makes it easy to create and share custom web apps for data science. 

The following code inserts a button allowing to download a PDF file:

```python
from fpdf import FPDF
import streamlit as st

st.title('Demo of fpdf2 usage with streamlit')

@st.cache
def gen_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.cell(txt="hello world")
    return bytes(pdf.output())

st.download_button(
    label="Download PDF",
    data=gen_pdf(),
    file_name="file_name.pdf",
    mime="application/pdf",
)
```

## web2py ##
Usage of the original PyFPDF lib with [web2py](http://www.web2py.com/) is described here: <https://github.com/reingart/pyfpdf/blob/master/docs/Web2Py.md>

`v1.7.2` of PyFPDF is included in `web2py` since release `1.85.2`: <https://github.com/web2py/web2py/tree/master/gluon/contrib/fpdf>
