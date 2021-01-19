## alias_nb_pages ##

```python
fpdf.alias_nb_pages()
```

### Description ###

Defines an alias for the total number of pages. It will be substituted as the document is closed.

This is useful if you have a "dynamic" number of pages,
and do not know the exact final number of pages of the document you are creating
at the time you are generating the pages.

**Note**: when using this feature with the `cell` / `multicell` methods, or the `underline` attribute of `FPDF` class,
the width of the text rendered will take into account the alias length, not the length of the "actual number of pages" string,
which can causes slight positioning differences.

### Parameters ###

alias:
> The alias. Default value: {nb}.

### Example ###
```python
class PDF(FPDF):
    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Select helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        # Print current and total page numbers
        self.cell(0, 10, 'Page %s' % self.page_no() + '/{nb}', 0, 0, 'C')

pdf = PDF()
pdf.alias_nb_pages()

```

### See also ###

[page_no](page_no.md), [footer](footer.md).
