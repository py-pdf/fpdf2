# OutputIntends #

## Embedded OutputIntends

> Embedded OutputIntends [allow] the contents of referenced icc profiles to be embedded directly within the body of the PDF file. This makes the PDF file a self-contained unit that can be stored or transmitted as a single entity.

`fpdf2` gives access to this feature through the method `set_output_intents()`:

Adds Desired Output Intent to the Output Intents Array:

Allowed Args:
- subtype (required) : PDFA, PDFX or ISOPDF
- output_condition_identifier (required): see the Name in https://www.color.org/registry.xalter
- output_condition (optional): see the Definition in https://www.color.org/registry.xalter
- registry_name (optional): https://www.color.org info (required/optional see dest_output_profile): String
- dest_output_profile: (required if output_condition_identifier does not specify a standard production condition; optional otherwise): None | FPDF.dest_output_profile(
    - fn=Path to ICC Profile,
    - N=[1|3|4], # depends on the numbers for colors 1=Gray, 3=RGB, 4=CMYK
    - alternate=['DeviceGray'|'DeviceRGB'|'DeviceCMYK']
    )

```python
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import OutputIntentSubType

HERE = Path(__file__).resolve().parent

pdf = FPDF()
pdf.set_output_intents(
        OutputIntentSubType.PDFA,
        "sRGB",
        'IEC 61966-2-1:1999',
        "http://www.color.org",
        FPDF.dest_output_profile(fn=HERE / "sRGB2014.icc", N=3,
                                 alternate="DeviceRGB"),
        "sRGB2014 (v2)",
    )
```

The needed profiles and descriptions can be found at [International Color Consortium](https://color.org/).