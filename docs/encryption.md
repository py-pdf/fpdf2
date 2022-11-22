# Encryption #

A PDF document can be encrypted to protect it's contents.

An owner password is mandatory. Using the owner password anyone can perform any change on the document, including removing all encryption and access permissions.

The optional parameters are user password, access permissions and encryption method.

## Password locking ##

User password is optional. If none is provided the document content is accessible for everyone.

If a user password is set, the content of the document will be encrypted and a password prompt displayed when a user opens the document. The document will only be displayed after either the user or owner password is entered.

```python
pdf.set_encryption(
    owner_password="foo",
    user_password="bar"
)
```

## Access permissions ##

Using access permissions flags you can restrict how the user interact with the document. The available access permission flags are:

  * `PRINT_LOW_RES`
    Print the document, limiting the quality of the printed version.

  * `PRINT_HIGH_RES`
    Print the document at the highest quality.

  * `MODIFY`
    Modify the contents of the document.

  * `COPY`
    Copy or extract text and graphics from the document.

  * `ANNOTATION`
    Add or modify text annotations.

  * `FILL_FORMS`
    Fill in existing interactive form fields.

  * `COPY_FOR_ACCESSIBILITY`
    Extract text and graphics in support of accessibility to users with disabilities
  
  * `ASSEMBLE`
    Insert, rotate or delete pages and create bookmarks or thumbnail images.

The flags can be combined using `|`:

```python
from fpdf import FPDF
from fpdf.enums import AccessPermission

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)
pdf.cell(txt="hello world")

pdf.set_encryption(
    owner_password="98765421",
    permissions=AccessPermission.PRINT_LOW_RES | AccessPermission.PRINT_HIGH_RES
)

pdf.output("output.pdf")
```

The method `all()` grants all permissions and `none()` denies all permissions.

```python
pdf.set_encryption(
    owner_password="xyz",
    permissions=AccessPermission.all()
)
```

If no permission is specified it will default to `all()`.

## Encryption method ##

There are 3 available encryption methods:

  * `NO_ENCRYPTION`
    Data is not encrypted, only add the access permission flags.

  * `RC4` (default)
    Default PDF encryption algorithm.

  * `AES_128`
    Encrypts the data with AES algorithm. Requires the `cryptography` package.

```python
from fpdf import FPDF
from fpdf.enums import AccessPermission, EncryptionMethod

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)
pdf.cell(txt="hello world")

pdf.set_encryption(
    owner_password="123",
    encryption_method=EncryptionMethod.AES_128,
    permissions=AccessPermission.none()
)

pdf.output("output.pdf")
```