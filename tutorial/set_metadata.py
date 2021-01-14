#!/usr/bin/env python3
import sys
from datetime import datetime
from fpdf import FPDF_VERSION
import pikepdf

with pikepdf.open(sys.argv[1], allow_overwriting_input=True) as pdf:
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:title"] = "Title"
        meta["dc:description"] = "Description"
        meta["dc:creator"] = "Author"
        meta["pdf:Keywords"] = "keyword1 keyword2 keyword3"
        meta["pdf:Producer"] = "PyFPDF/fpdf{}".format(FPDF_VERSION)
        meta["xmp:CreatorTool"] = __file__
        meta["xmp:MetadataDate"] = datetime.now(
            datetime.utcnow().astimezone().tzinfo
        ).isoformat()
    pdf.save()
