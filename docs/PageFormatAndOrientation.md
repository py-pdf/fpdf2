# Page format and orientation #

By default, a `FPDF` document has a [`A4`](https://en.wikipedia.org/wiki/ISO_216#A_series) format with `portrait` orientation.

Other formats & orientation can be specified to `FPDF` constructor:

```python
pdf = fpdf.FPDF(orientation="landscape", format="A5")
```

Currently supported formats are `a3`, `a4`, `a5`, `letter` & `legal`.
Additional formats are welcome and can be suggested through pull requests.
