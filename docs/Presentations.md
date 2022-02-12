# Presentations

**Presentation mode** can usually be enabled with the `CTRL + L` shortcut.

As of june 2021, the features described below are onored by Adobe Acrobat reader,
but ignored by Sumatra PDF reader.

## Page display duration

Pages can be associated with a "display duration"
until when the viewer application automatically advances to the next page:

```python
from fpdf import FPDF

pdf = fpdf.FPDF()
pdf.set_font("Helvetica", size=120)
pdf.add_page(duration=3)
pdf.cell(txt="Page 1")
pdf.page_duration = .5
pdf.add_page()
pdf.cell(txt="Page 2")
pdf.add_page()
pdf.cell(txt="Page 3")
pdf.output("presentation.pdf")
```

It can also be configured globally through the `page_duration` FPDF property.

## Transitions

Pages can be associated with visual transitions to use when moving
from another page to the given page during a presentation:

```python
from fpdf import FPDF
from fpdf.transitions import *

pdf = fpdf.FPDF()
pdf.set_font("Helvetica", size=120)
pdf.add_page()
pdf.text(x=40, y=150, txt="Page 0")
pdf.add_page(transition=SplitTransition("V", "O"))
pdf.text(x=40, y=150, txt="Page 1")
pdf.add_page(transition=BlindsTransition("H"))
pdf.text(x=40, y=150, txt="Page 2")
pdf.add_page(transition=BoxTransition("I"))
pdf.text(x=40, y=150, txt="Page 3")
pdf.add_page(transition=WipeTransition(90))
pdf.text(x=40, y=150, txt="Page 4")
pdf.add_page(transition=DissolveTransition())
pdf.text(x=40, y=150, txt="Page 5")
pdf.add_page(transition=GlitterTransition(315))
pdf.text(x=40, y=150, txt="Page 6")
pdf.add_page(transition=FlyTransition("H"))
pdf.text(x=40, y=150, txt="Page 7")
pdf.add_page(transition=PushTransition(270))
pdf.text(x=40, y=150, txt="Page 8")
pdf.add_page(transition=CoverTransition(270))
pdf.text(x=40, y=150, txt="Page 9")
pdf.add_page(transition=UncoverTransition(270))
pdf.text(x=40, y=150, txt="Page 10")
pdf.add_page(transition=FadeTransition())
pdf.text(x=40, y=150, txt="Page 11")
pdf.output("transitions.pdf")
```

It can also be configured globally through the `page_transition` FPDF property.
