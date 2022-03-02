# Page breaks #

By default, `fpdf2` will automatically perform page breaks whenever a cell or
the text from a `write()` is rendered at the bottom of a page with a height
greater than the page bottom margin.

This behaviour can be controlled using the
[`set_auto_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break)
and
[`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break)
methods.


## Manually trigger a page break ##

Simply call `.add_page()`.


## Unbreakable sections ##

In order to render content, like [tables](Tables.md),
with the insurance that no page break will be performed in it,
on the can use the `FPDF.unbreakable()` context-manager:

```python
pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Times", size=16)
line_height = pdf.font_size * 2
col_width = pdf.epw / 4  # distribute content evenly
for i in range(4):  # repeat table 4 times
    with pdf.unbreakable() as pdf:
        for row in data:  # data comes from snippets on the Tables documentation page
            for datum in row:
                pdf.cell(col_width, line_height, f"{datum} ({i})", border=1)
            pdf.ln(line_height)
    pdf.ln(line_height * 2)
pdf.("unbreakable_tables.pdf")
```
