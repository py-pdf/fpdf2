# Templating with Jinja #

> [Jinja](https://jinja.palletsprojects.com/) is a fast, expressive, extensible templating engine.


## Combining Jinja & write_html

```python
from fpdf import FPDF
from jinja2 import Environment

template = Environment().from_string("""
<h1>{{ title | escape }}</h1>
<ul>
{% for item in items %}
  <li>{{ item }}</li>
{% endfor %}
</ul>
""")

title = "HTML & Jinja demo"
items = [
    "FIRST",
    "SECOND",
    "LAST"
]

pdf = FPDF()
pdf.add_page()
pdf.write_html(template.render(**globals()))
pdf.output("templating_with_jinja.pdf")
```

More details about the supported HTML features: [HTML](HTML.md)
