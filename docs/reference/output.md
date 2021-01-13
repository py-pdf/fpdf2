## output ##

```python
fpdf.output(name = '')
```

### Description ###

Send the document to some destination: standard output, a file or a byte string.

The method first calls [close](close.md) if necessary to terminate the document.

**NOTICE:**
In Python 2 strings were raw data but in Python 3 strings are now unicode by default. If you are using Python 3.x you have to use `pdf.output().encode('latin-1')` in order to get the output, if you don't do so the generated PDF will be invalid and depending on the viewer either not open at all or show up as some blank pages.

### Parameters ###

name:
> The name of the file. Only used when writing to a file.

### See also ###

[close](close.md).
