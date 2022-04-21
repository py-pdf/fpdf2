# Line breaks #

When using [multi_cell()](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) or
[write()](fpdf/fpdf.html#fpdf.fpdf.FPDF.write), each time a line reaches the
right extremity of the cell or a carriage return character (`\n`) is met, a
line break is issued and a new line automatically created under the current
one.

An automatic break is performed at the location of the nearest space or soft-hyphen (`\u00ad`) character before the right limit.
A soft-hyphen will be replaced by a normal hyphen when triggering a line break, and ignored otherwise.

If the parameter `print_sh=False` in `multi_cell()` or `write()` is set to `True`, then they will print the soft-hyphen character to the document (as a normal hyphen with most fonts) instead of using it as a line break opportunity.
