# Page breaks #

By default, `fpdf2` will automatically perform page breaks whenever a cell or
the text from a `write()` is rendered at the bottom of a page with a height
greater than the page bottom margin.

This behaviour can be controlled using those methods:

* [`set_auto_page_break`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break)
* [`accept_page_break`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break)
* [`will_page_break`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.will_page_break)


## Manually trigger a page break ##

Simply call `.add_page()`.


## Inserting the final number of pages of the document ##

The special string `{nb}` will be substituted by the total number of pages on document closure.
This special value can be configured or changed by calling [alias_nb_pages()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages):

```python
pdf.alias_nb_pages(alias="{nb}", align="L")
```

### Alignment control for alias substitution

[**NEW in 2.8.9**] `alias_nb_pages()` supports an optional `align` parameter (`"L"`, `"C"`, `"R"`, or `Align.L`, `Align.C`, `Align.R`).
The default alignment is `"L"` (left-aligned).

When the layout is calculated, `fpdf2` reserves horizontal space based on the length of the alias string (e.g. `{nb}` reserves space for up to 2-digit numbers; custom aliases like `{total_pages}` reserve more space). When the final page count is substituted, `align` controls how the substitution text is positioned within that reserved space:

* `align="L"` / `Align.L`: text stays left-aligned in the reserved space (default).
* `align="C"` / `Align.C`: text is horizontally centered within the reserved space.
* `align="R"` / `Align.R`: text is right-aligned in the reserved space.

> **Note**: `Align.J` (justification) is not applicable to page number alias substitution and will emit a `UserWarning` falling back to `Align.L`. `Align.X` is treated as `Align.C`.

Example footer with centered page number alias:
```python
class MyPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

pdf = MyPDF()
pdf.alias_nb_pages(alias="{nb}", align="C")
```


## will_page_break ##

`will_page_break(height)` lets you know if adding an element will trigger a page break,
based on its `height` and the current ordinate (`y` position).


## Unbreakable sections ##

In order to render content, like [tables](Tables.md),
with the insurance that no page break will be performed in it,
one can use the `FPDF.unbreakable()` context-manager:

```python
pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Times", size=16)
line_height = pdf.font_size * 2
col_width = pdf.epw / 4  # distribute content evenly
for i in range(4):  # repeat table 4 times
    with pdf.unbreakable() as doc:
        for row in data:  # data comes from snippets on the Tables documentation page
            for datum in row:
                doc.cell(col_width, line_height, f"{datum} ({i})", border=1)
            doc.ln(line_height)
    print('page_break_triggered:', doc.page_break_triggered)
    pdf.ln(line_height * 2)
pdf.output("unbreakable_tables.pdf")
```

An alternative approach is [`offset_rendering()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.offset_rendering)
that allows to test the results of some operations on the global layout
before performing them "for real":

```python
with pdf.offset_rendering() as dummy:
    # Dummy rendering:
    dummy.multi_cell(...)
if dummy.page_break_triggered:
    # We trigger a page break manually beforehand:
    pdf.add_page()
    # We duplicate the section header:
    pdf.cell(text="Appendix C")
# Now performing our rendering for real:
pdf.multi_cell(...)
```