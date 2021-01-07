## footer ##

```python
fpdf.footer()
```

### Description ###

This method is used to render the page footer. It is automatically called by [add_page](add_page.md) and [close](close.md) and should not be called directly by the application. The implementation in FPDF is empty, so you have to subclass it and override the method if you want a specific processing.

### Example ###
```python
class PDF(FPDF):
    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Select Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Print centered page number
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')
```

### See also ###

[add_page](add_page.md), [header](header.md).
