# Signing #

> A digital signature may be used to authenticate the identity of a user and the document’s contents.> It stores information about the signer and the state of the document when it was signed.

`fpdf2` allows to **sign** documents using [PKCS12](https://en.wikipedia.org/wiki/PKCS_12) certificates ([RFC 7292](https://datatracker.ietf.org/doc/html/rfc7292)).
The [endesive](https://pypi.org/project/endesive/) package is **required** to do so.

```python
pdf = FPDF()
pdf.add_page()
pdf.sign_pkcs12("certs.p12", password=b"1234")
pdf.output("signed_doc.pdf")
```
