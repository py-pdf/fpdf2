# Pystrich #

`fpdf2` can easily be used with the `pystrich` library to generate barcodes. `pystrich` generates barcode images in the form of a pilimage, which are then inserted into the pdf file via the `image` function.


## DataMatrix Example ##

The following example demonstrates how to use the `pystrich` library to insert a datamatrix barcode into a FPDF file.

```python
from fpdf import FPDF
from pystrich.datamatrix import DataMatrixEncoder, DataMatrixRenderer


# Define the properties of the barcode
positionX = 10
positionY = 10
width = 57
height = 57
cellsize = 5

# Prepare the datamatrix renderer that will be used to generate the pilimage
encoder = DataMatrixEncoder("[Text to be converted to a datamatrix barcode]")
encoder.width = width
encoder.height = height
renderer = DataMatrixRenderer(encoder.matrix, encoder.regions)

# Generate a pilimage and move it into the memory stream
pilImage = renderer.get_pilimage(cellsize)


# Draw the barcode image into a pdf file
pdfFile = FPDF()
pdfFile.add_page()
pdfFile.image(pilImage, positionX, positionY, width, height)
```

## Add as Extension method ##

The code above could be added to the FPDF class as an extension method in the following way.

```python
from fpdf import FPDF
from pystrich.datamatrix import DataMatrixEncoder, DataMatrixRenderer


def datamatrix(self, text='', x=0, y=0, w=57, h=57, cellsize=5):
    "Convert text to a datamatrix barcode and put in on the page"

    encoder = DataMatrixEncoder(text)
    encoder.width = w
    encoder.height = h
    renderer = DataMatrixRenderer(encoder.matrix, encoder.regions)
    
    pilImage = renderer.get_pilimage(cellsize)

    self.image(pilImage, x, y, w, h)

FPDF.datamatrix = datamatrix
del(datamatrix)
```
