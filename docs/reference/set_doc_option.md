## set_doc_option ##

```python
fpdf.set_doc_option(opt: str, value)
```
[TOC]

### Description ###

Defines the document option.

### Parameters ###

opt:
> Option to set.

value:
> Value.

### Options ###

#### core_fonts_encoding ####

Specify encoding used for decoding unicode text for standard (non-unicode) 
fonts. Supported values are `latin-1` and `windows-1252`. Set this option 
before using any text writing.

### See also ###

[set_font](set_font.md), [write](write.md).
