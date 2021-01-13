## alias_nb_pages ##

```python
fpdf.alias_nb_pages()
```

### Description ###

Defines an alias for the total number of pages. It will be substituted as the document is closed.

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
