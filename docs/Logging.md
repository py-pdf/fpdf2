# Logging #

`fpdf.FPDF` generates useful `DEBUG` logs on generated sections sizes
when calling the `output()` method., that can help to identify what part of a PDF
takes most space (fonts, images, pages...).

Here is an example of setup code to display them:

```python
import logging

logging.basicConfig(format="%(asctime)s %(filename)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S", level=logging.DEBUG)
```

Example output using the [Tutorial](Tutorial.md) first code snippet:

    14:09:56 fpdf.py [DEBUG] Final doc sections size summary:
    14:09:56 fpdf.py [DEBUG] - header.size: 9.0B
    14:09:56 fpdf.py [DEBUG] - pages.size: 306.0B
    14:09:56 fpdf.py [DEBUG] - resources.fonts.size: 101.0B
    14:09:56 fpdf.py [DEBUG] - resources.images.size: 0.0B
    14:09:56 fpdf.py [DEBUG] - resources.dict.size: 104.0B
    14:09:56 fpdf.py [DEBUG] - info.size: 54.0B
    14:09:56 fpdf.py [DEBUG] - catalog.size: 103.0B
    14:09:56 fpdf.py [DEBUG] - xref.size: 169.0B
    14:09:56 fpdf.py [DEBUG] - trailer.size: 60.0B

## See also ##
[Tutorial](Tutorial.md), [ReferenceManual](reference),
[Unicode](Unicode.md).
