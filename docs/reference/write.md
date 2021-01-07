## write ##

```python
write(h: float, txt: str, link)
```

### Description ###

This method prints text from the current position. When the right margin is 
reached (or the \n character is met), a line break occurs and text continues 
from the left margin. Upon method exit, the current position is left just at 
the end of the text.

It is possible to put a link on the text.

### Parameters ###

h:
> Line height.

txt:
> String to print.

link:
> URL or identifier returned by [add_link](add_link.md).

### Example ###
```python
# Begin with regular font
pdf.set_font('Arial', '', 14)
pdf.write(5, 'Visit ')
# Then put a blue underlined link
pdf.set_text_color(0, 0, 255)
pdf.set_font('', 'U')
pdf.write(5, 'www.fpdf.org', 'http://www.fpdf.org')
```

### See also ###

[set_doc_option](set_doc_option.md), [set_font](set_font.md), 
[set_text_color](set_text_color.md), [add_link](add_link.md), 
[multi_cell](multi_cell.md), [set_auto_page_break](set_auto_page_break.md), 
[write_html](write_html.md)
