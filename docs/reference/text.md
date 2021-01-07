## text ##

```python
fpdf.text(x: float, y: float, txt: str)
```
### Description ###

Prints a character string. The origin is on the left of the first character, on 
the baseline. This method allows placing a string precisely on the page, but it 
is usually easier to use [cell](cell.md), [multi_cell](multi_cell.md) or 
[write](write.md), which are the standard methods to print text.

### Parameters ###

x:
> Abscissa of the origin.

y:
> Ordinate of the origin.

txt:
> String to print.

### See also ###

[set_doc_option](set_doc_option.md), [set_font](set_font.md), 
[set_text_color](set_text_color.md), [cell](cell.md), 
[multi_cell](multi_cell.md), [write](write.md).
