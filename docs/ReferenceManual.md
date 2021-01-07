# PyFPDF Reference Manual #

[TOC]

## fpdf Python API ##

### Classes ###
  * [FPDF](reference/FPDF.md) - constructor

### Methods ###
#### Pages ####
  * [add_page](reference/add_page.md) - add a new page
  * [page_no](reference/page_no.md) - page number
  * [alias_nb_pages](reference/alias_nb_pages.md) - define an alias for number of pages
  * [close](reference/close.md) - terminate the document *(internal api)*
  * [output](reference/output.md) - save or send the document
  * [header](reference/header.md) - page header
  * [footer](reference/footer.md) - page footer

#### Margins ####
  * [set_margins](reference/set_margins.md) - set margins
  * [set_left_margin](reference/set_left_margin.md) - set left margin
  * [set_right_margin](reference/set_right_margin.md) - set right margin
  * [set_top_margin](reference/set_top_margin.md) - set top margin
  * [set_auto_page_break](reference/set_auto_page_break.md) - set the automatic page breaking mode

#### Fonts ####
  * [add_font](reference/add_font.md) - add a new font
  * [set_font](reference/set_font.md) - set font
  * [set_font_size](reference/set_font_size.md) - set font size
  
#### Links ####
  * [link](reference/link.md) - put a link
  * [add_link](reference/add_link.md) - create an internal link
  * [set_link](reference/set_link.md) - set internal link destination
  
#### Metadata ####
  * [set_author](reference/set_author.md) - set the document author
  * [set_compression](reference/set_compression.md) - turn compression on or off
  * [set_creator](reference/set_creator.md) - set document creator
  * [set_keywords](reference/set_keywords.md) - associate keywords with document
  * [set_subject](reference/set_subject.md) - set document subject
  * [set_title](reference/set_title.md) - set document title
  * [set_display_mode](reference/set_display_mode.md) - set display mode

#### Text ####
  * [text](reference/text.md) - print a string
  * [write](reference/write.md) - print flowing text
  * [cell](reference/cell.md) - print a cell
  * [multi_cell](reference/multi_cell.md) - print text with line breaks
  * [get_string_width](reference/get_string_width.md) - compute string length
  * [ln](reference/ln.md) - line break
  * [set_line_width](reference/set_line_width.md) - set line width

#### Geometry ####
  * [get_x](reference/get_x.md) - get current x position
  * [get_y](reference/get_y.md) - get current y position
  * [set_x](reference/set_x.md) - set current x position
  * [set_xy](reference/set_xy.md) - set current x and y positions
  * [set_y](reference/set_y.md) - set current y position
  * [line](reference/line.md) - draw a line
  * [rect](reference/rect.md) - draw a rectangle

#### Colors ####
  * [set_draw_color](reference/set_draw_color.md) - set drawing color
  * [set_fill_color](reference/set_fill_color.md) - set filling color
  * [set_text_color](reference/set_text_color.md) - set text color

#### Imaging ####
  * [image](reference/image.md) - output an image


## Original FPDF API ##

**Important**: the original FPDF (PHP) naming convention is CamelCase. This library uses [PEP8's](http://www.python.org/dev/peps/pep-0008/) lower\_case\_with\_underscores recommendation.

The contents of this section are the same as those of the previous section except organized like the PHP Library. This is also the format that was used in versions 1.x.x of this library. For the [PHP documentation](http://www.fpdf.org/en/doc/index.php) refer to the [FPDF](http://www.fpdf.org/) website.

  * [accept_page_break](reference/accept_page_break.md) - determine whether to issue automatic page break
  * [add_font](reference/add_font.md) - add a new font
  * [add_link](reference/add_link.md) - create an internal link
  * [add_page](reference/add_page.md) - add a new page
  * [alias_nb_pages](reference/alias_nb_pages.md) - define an alias for number of pages
  * [cell](reference/cell.md) - print a cell
  * [close](reference/close.md) - terminate the document
  * [error](reference/error.md) - fatal error
  * [footer](reference/footer.md) - page footer
  * [FPDF](reference/FPDF.md) - constructor
  * [get_string_width](reference/get_string_width.md) - compute string length
  * [get_x](reference/get_x.md) - get current x position
  * [get_y](reference/get_y.md) - get current y position
  * [header](reference/header.md) - page header
  * [image](reference/image.md) - output an image
  * [line](reference/line.md) - draw a line
  * [link](reference/link.md) - put a link
  * [ln](reference/ln.md) - line break
  * [multi_cell](reference/multi_cell.md) - print text with line breaks
  * [output](reference/output.md) - save or send the document
  * [page_no](reference/page_no.md) - page number
  * [rect](reference/rect.md) - draw a rectangle
  * [set_author](reference/set_author.md) - set the document author
  * [set_auto_page_break](reference/set_auto_page_break.md) - set the automatic page breaking mode
  * [set_compression](reference/set_compression.md) - turn compression on or off
  * [set_creator](reference/set_creator.md) - set document creator
  * [set_display_mode](reference/set_display_mode.md) - set display mode
  * [set_draw_color](reference/set_draw_color.md) - set drawing color
  * [set_fill_color](reference/set_fill_color.md) - set filling color
  * [set_font](reference/set_font.md) - set font
  * [set_font_size](reference/set_font_size.md) - set font size
  * [set_keywords](reference/set_keywords.md) - associate keywords with document
  * [set_left_margin](reference/set_left_margin.md) - set left margin
  * [set_line_width](reference/set_line_width.md) - set line width
  * [set_link](reference/set_link.md) - set internal link destination
  * [set_margins](reference/set_margins.md) - set margins
  * [set_right_margin](reference/set_right_margin.md) - set right margin
  * [set_subject](reference/set_subject.md) - set document subject
  * [set_text_color](reference/set_text_color.md) - set text color
  * [set_title](reference/set_title.md) - set document title
  * [set_top_margin](reference/set_top_margin.md) - set top margin
  * [set_x](reference/set_x.md) - set current x position
  * [set_xy](reference/set_xy.md) - set current x and y positions
  * [set_y](reference/set_y.md) - set current y position
  * [text](reference/text.md) - print a string
  * [write](reference/write.md) - print flowing text

## Additional API ##
  
These features are not available in the original FPDF and were implemented after forking.

  * [dashed_line](reference/dashed_line.md) - draw a dashed line
  * [ellipse](reference/ellipse.md) - draw an ellipse
  * [rotate](reference/rotate.md) - rotation around a given center
  * [set_doc_option](reference/set_doc_option.md) - set document options
  * [set_stretching](reference/set_stretching.md) - set horizontal font stretching
  * [write_html](reference/write_html.md) - print text with HTML markup ***Obsolete, under review.***
