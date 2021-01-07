## close ##

```python
fpdf.close()
```

### Description ###

Terminates the PDF document. It is not necessary to call this method explicitly because [output](output.md) does it automatically. 
If the document contains no page, [add_page](add_page.md) is called to prevent from getting an invalid document.


### See also ###

[open](open.md), [output](output.md).
