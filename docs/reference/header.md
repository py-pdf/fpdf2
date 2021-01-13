## header ##

```python
fpdf.header()
```

### Description ###

This method is used to render the page header. It is automatically called by [add_page](add_page.md) and should not be called directly by the application. The implementation in FPDF is empty, so you have to subclass it and override the method if you want a specific processing.

### Example ###

```python
class PDF(FPDF):
    def header(self):
        # Select helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Move to the right
        self.cell(80)
        # Framed title
        self.cell(30, 10, 'Title', 1, 0, 'C')
        # Line break
        self.ln(20)
```

### See also ###

[add_page](add_page.md), [footer](footer.md).
