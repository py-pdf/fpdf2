# Usage in web API #


## Django ##

Usage in a [view](https://docs.djangoproject.com/en/4.0/topics/http/views/):

```python
from fpdf import FPDF
from django.http import HttpResponse


def report(request):
    pdf = FPDF()
    ...
    return HttpResponse(bytes(pdf.output()), content_type='application/pdf')
```


## web2py ##

Usage of the original PyFPDF lib with [web2py](http://www.web2py.com/) is described here: <https://github.com/reingart/pyfpdf/blob/master/docs/Web2Py.md>

`v1.7.2` of PyFPDF is included in `web2py` since release `1.85.2`: <https://github.com/web2py/web2py/tree/master/gluon/contrib/fpdf>
