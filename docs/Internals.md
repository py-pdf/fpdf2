# fpdf2 internals

## FPDF.pages
`FPDF` is designed to add content progressively to the document generated, page by page.

Each page is an entry in the `.pages` attribute of `FPDF` instances.
Indices start at 1 (the first page) and values are [`PDFPage`](https://py-pdf.github.io/fpdf2/fpdf/output.html#fpdf.output.PDFPage) instances.

`PDFPage` instances have a `.contents` attribute that is a [`bytearray`](https://docs.python.org/3/library/stdtypes.html#bytearray) and contains the **Content Stream** for this page
(`bytearray` makes things [a lot faster](https://github.com/reingart/pyfpdf/pull/164)).

Going back to a previously generated page to add content is possible,
using the [`.page` attribute](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.page), but may result in unexpected behavior, because [.add_page()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page) takes special care to ensure the page's content stream matches `FPDF`'s instance attributes.


## syntax.py & objects serialization
The [syntax.py](https://github.com/py-pdf/fpdf2/blob/master/fpdf/syntax.py) package contains classes representing core elements of the PDF syntax.

Classes inherit from the [PDFObject](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.PDFObject) class, that has the following properties:

* every PDF object has an `.id`, that is assigned during the document serialization by the [OutputProducer](#outputproducer)
* the `.serialize()` method renders the PDF object as an `obj<<...>>endobj` text block. It can be overridden by child classes
* the `.content_stream()` method must return non empty bytes if the PDF Object has a _content stream_

Other notable core classes are:

* [Name](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.Name)
* [Raw](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.Raw)
* [PDFString](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.PDFString)
* [PDFArray](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.PDFArray)
* [PDFDate](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.syntax.PDFDate)


## GraphicsStateMixin
This _mixin_ class, inherited by the `FPDF` class,
allows to manage a stack of graphics state variables:

* docstring: [fpdf.graphics_state.GraphicsStateMixin](https://py-pdf.github.io/fpdf2/fpdf/graphics_state.html#fpdf.graphics_state.GraphicsStateMixin)
* source file: [graphics_state.py](https://github.com/py-pdf/fpdf2/blob/master/fpdf/graphics_state.py)

The main methods of this API are:

* [_push_local_stack()](https://py-pdf.github.io/fpdf2/fpdf/graphics_state.html#fpdf.graphics_state.GraphicsStateMixin._push_local_stack): Push a graphics state on the stack
* [_pop_local_stack()](https://py-pdf.github.io/fpdf2/fpdf/graphics_state.html#fpdf.graphics_state.GraphicsStateMixin._pop_local_stack): Pop the last graphics state on the stack
* [_get_current_graphics_state()](https://py-pdf.github.io/fpdf2/fpdf/graphics_state.html#fpdf.graphics_state.GraphicsStateMixin._get_current_graphics_state): Retrieve the current graphics state
* [_is_current_graphics_state_nested()](https://py-pdf.github.io/fpdf2/fpdf/graphics_state.html#fpdf.graphics_state.GraphicsStateMixin._is_current_graphics_state_nested): Indicate if the stack contains items (else it is empty)

Thanks to this _mixin_, we can use the following semantics:
```python
{% include "../tutorial/graphics_state.py" %}
```

The graphics states used in the code above
can be depicted by this diagram:

``` mermaid
stateDiagram-v2
  direction LR
  state gs0 {
    initial1 : Base state
  }
  state gs1 {
    initial2 : Base state
    font_size_pt2 : font_size_pt=16
    underline2 : underline=True
    font_size_pt2 --> initial2
    underline2 --> font_size_pt2
  }
  gs0 --> gs1: Step 1
  state "gs0" as stack2 {
    initial3 : Base state
  }
  gs1 --> stack2: Step 2
```


## OutputProducer
In `fpdf2`, the `FPDF` class is used to store the document **definition**,
its state as it is progressively built. Most attributes and internal data is **mutable**.

Once it's done, when the [FPDF.output()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output) method is called, the actual PDF file creation is delegated to the [OutputProducer](https://py-pdf.github.io/fpdf2/fpdf/output.html#fpdf.output.OutputProducer) class.

It performs the serialization of the PDF document,
including the generation of the [cross-reference table & file trailer](https://py-pdf.github.io/fpdf2/fpdf/output.html#fpdf.output.PDFXrefAndTrailer).
This class uses the `FPDF` instance as **immutable input**:
it does not perform any modification on it.

<!-- Other topics to mention:

## Vector Graphics
drawing.py & svg.py packages

## Text regions & flow ?

## Text shaping ?

+ add a diagram of the main links between modules/classes
-->
