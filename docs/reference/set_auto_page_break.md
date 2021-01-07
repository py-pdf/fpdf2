## set_auto_page_break ##

```python
fpdf.set_auto_page_break(auto: bool, margin = 0.0)
```

### Description ###

Enables or disables the automatic page breaking mode. When enabling, the second parameter is the distance from the bottom of the page that defines the triggering limit. By default, the mode is on and the margin is 2 cm.

### Parameters ###

auto:
> Boolean indicating if mode should be on or off.

margin:
> Distance from the bottom of the page.

### See also ###

[cell](cell.md), [multi_cell](multi_cell.md), [accept_page_break](accept_page_break.md).
