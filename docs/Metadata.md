# Metadata #

The PDF specification contain two types of metadata, the newer XMP
(Extensible Metadata Platform, XML-based) and older `DocumentInformation` dictionary.
The PDF 2.0 specification removes the `DocumentInformation` dictionary.

Currently, the following methods on `fpdf.FPDF` allow to set metadata information
in the `DocumentInformation` dictionary:

- `set_title`
- `set_lang`
- `set_subject`
- `set_author`
- `set_keywords`
- `set_producer`
- `set_creator`
- `set_creation_date`
- `set_xmp_metadata`, that requires you to craft the necessary XML string

For a more user-friendly API to set metadata,
we recommend using [`pikepdf`](https://github.com/pikepdf/pikepdf/) that will set both XMP & `DocumentInformation` metadata:

```python
import sys
from datetime import datetime

import pikepdf
from fpdf import FPDF_VERSION

with pikepdf.open(sys.argv[1], allow_overwriting_input=True) as pdf:
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:title"] = "Title"
        meta["dc:description"] = "Description"
        meta["dc:creator"] = "Author"
        meta["pdf:Keywords"] = "keyword1 keyword2 keyword3"
        meta["pdf:Producer"] = f"PyFPDF/fpdf{FPDF_VERSION}"
        meta["xmp:CreatorTool"] = __file__
        meta["xmp:MetadataDate"] = datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
    pdf.save()
```
