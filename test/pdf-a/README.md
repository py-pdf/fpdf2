All files in this directory should be PDF-A compliant.

This can be ensured using [VeraPDF](https://verapdf.org/),
by calling those scripts from the repository root directory:

    scripts/install-verapdf.sh
    scripts/check-PDF-A-with-verapdf.sh

`pikepdf` also checks if the PDF **claims** to be conformant:
https://pikepdf.readthedocs.io/en/latest/topics/metadata.html#checking-pdf-a-conformance
It is used in unit tests by checking PDF metadata `.pdfa_status`.
