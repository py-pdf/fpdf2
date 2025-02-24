# Output Intends #

> Output Intends [allow] the contents of referenced icc profiles to be embedded directly within the body of the PDF file. This makes the PDF file a self-contained unit that can be stored or transmitted as a single entity.

## Add Desired Output Intent to the Output Intents Array ##
`fpdf2` gives access to this feature through the method [`set_output_intent()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_output_intent):

### Specify ICCProfile Stream ###
[`ICCProfileStreamDict`](https://py-pdf.github.io/fpdf2/fpdf/output.html#fpdf.output.output.ICCProfileStreamDict) Class is needed to specify the file object of the referenced icc profile.


```python
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import OutputIntentSubType
from fpdf.output import ICCProfileStreamDict

HERE = Path(__file__).resolve().parent

pdf = FPDF()

dest_output_profile = ICCProfileStreamDict(
        fn=HERE / "sRGB2014.icc",
        N=3,
        alternate="DeviceRGB")

pdf.set_output_intent(
        OutputIntentSubType.PDFA,
        "sRGB",
        'IEC 61966-2-1:1999',
        "http://www.color.org",
        dest_output_profile,
        "sRGB2014 (v2)",
    )
```

The needed profiles and descriptions can be found at [International Color Consortium](https://color.org/).