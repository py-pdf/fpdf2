## accept_page_break ##

```python
fpdf.accept_page_break
```

### Description ###

`@property` method to determine whether to issue automatic page break.

Whenever a page break condition is met, this method is called, and the break is issued or not depending on the returned value.

The default implementation returns a value according to the mode selected by [set_auto_page_break](set_auto_page_break.md).
This method is called automatically and should not be called directly by the application.

### Example ###

From `tutorials/tuto4.py`:

```python
class PDF(FPDF):
    @property
    def accept_page_break(self):
        if self.col < 2:
            # Go to next column:
            self.set_col(self.col + 1)
            # Set ordinate to top:
            self.set_y(self.y0)
            # Stay on the same page:
            return False
        # Go back to first column:
        self.set_col(0)
        # Trigger a page break:
        return True
```

### See also ###

[set_auto_page_break](set_auto_page_break.md).
