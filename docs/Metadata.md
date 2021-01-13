# Metadata #

The PDF specification contain two types of metadata, the newer XMP
(Extensible Metadata Platform, XML-based) and older `DocumentInformation` dictionary.
The PDF 2.0 specification removes the `DocumentInformation` dictionary.

Currently, the following methods on `fpdf.FPDF` allow to set metadata information
in the `DocumentInformation` dictionary:

- `set_title`
- `set_subject`
- `set_author`
- `set_keywords`
- `set_creator`
- `set_creation_date`

In order to be fully compliant with the recent PDF specs,
we recommend using `pikepdf` that will set both XMP & `DocumentInformation` metadata:

```python
from datetime import datetime
from fpdf import FPDF_VERSION
import pikepdf

start_size = os.stat(filepath).st_size
with pikepdf.open(filepath, allow_overwriting_input=True) as pdf:
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta['dc:title'] = "Title"
        meta["dc:description"] = "Description"
        meta["dc:creator"] = "Author"
        meta["pdf:Keywords"] = "keyword1 keyword2 keyword3"
        meta["pdf:Producer"] = "PyFPDF/fpdf{}".format(FPDF_VERSION)
        meta["xmp:CreatorTool"] = __file__
        meta["xmp:MetadataDate"] = datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
    pdf.save()
end_size = os.stat(filepath).st_size
print(f"Final file size: {end_size / 1024**2:.0f}Mb (metada addition added {(end_size - start_size) / 1024**2:.0f}Mb)")
```
