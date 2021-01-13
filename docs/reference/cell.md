## cell ##

```python
fpdf.cell(w, h = 0, txt = '', border = 0, ln = 0, 
          align = '', fill = False, link = '')
```

### Description ###

Prints a cell (rectangular area) with optional borders, background color and 
character string. The upper-left corner of the cell corresponds to the current 
position. The text can be aligned or centered. After the call, the current 
position moves to the right or to the next line. It is possible to put a link 
on the text.

If automatic page breaking is enabled and the cell goes beyond the limit, a 
page break is done before outputting.

### Parameters ###

w:
> Cell width. If 0, the cell extends up to the right margin.

h:
> Cell height. Default value: 0.

txt:
> String to print. Default value: empty string.

border:
> Indicates if borders must be drawn around the cell. The value can be either a 
  number:
>>    * 0: no border
>>    * 1: frame
> 
> or a string containing some or all of the following characters (in any order):
>>    * `L`: left
>>    * `T`: top
>>    * `R`: right
>>    * `B`: bottom
> 
> Default value: 0.

ln:
> Indicates where the current position should go after the call. Possible 
  values are:
>>    * 0: to the right
>>    * 1: to the beginning of the next line
>>    * 2: below
> 
> Putting 1 is equivalent to putting 0 and calling [ln](ln.md) just after. 
  Default value: 0.

align:
> Allows to center or align the text. Possible values are:
>>    * `L` or empty string: left align (default value)
>>    * `C`: center
>>    * `R`: right align

fill:
> Indicates if the cell background must be painted (`True`) or transparent 
  (`False`). Default value: False.

link:
> URL or identifier returned by [add_link](add_link.md).

### Example ###

```python
# Set font
pdf.set_font('helvetica', 'B', 16)
# Move to 8 cm to the right
pdf.cell(80)
# Centered text in a framed 20*10 mm cell and line break
pdf.cell(20, 10, 'Title', 1, 1, 'C')
```

### See also ###

[set_font](set_font.md), [set_doc_option](set_doc_option.md), 
[set_draw_color](set_draw_color.md), [set_fill_color](set_fill_color.md), 
[set_text_color](set_text_color.md), [set_line_width](set_line_width.md), 
[add_link](add_link.md), [ln](ln.md), [multi_cell](multi_cell.md), 
[write](write.md), [set_auto_page_break](set_auto_page_break.md).
