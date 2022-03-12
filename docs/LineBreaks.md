# Line breaks #

When using [multi_cell()](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell), each time a line reaches the right extremity of the cell
or a carriage return character (`\n`) is met, a line break is issued and a new cell automatically created under the current one.

An automatic break is performed at the location of the nearest space or soft-hyphen (`\u00ad`) character before the right limit.
A soft-hyphen will be replaced by a normal hyphen when triggering a line break, and ignored otherwise.
