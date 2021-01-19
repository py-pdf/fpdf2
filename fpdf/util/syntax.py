"""PDF Syntax Helpers

Functions in this module take variable input and produce PDF Syntax features
as they are described in the Adobe PDF Reference Manual, found
[here](http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf).

Most of what happens in a PDF happens in objects, which are formatted like so:
<pre>
3 0 obj
<</Type /Page
/Parent 1 0 R
/Resources 2 0 R
/Contents 4 0 R>>
endobj
</pre>

The first line says that this is the third object in the structure of the
document.

There are 8 kinds of objects (Adobe Reference, 51):
* Boolean values
* Integer and real numbers
* Strings
* Names
* Arrays
* Dictionaries
* Streams
* The null object

The `<<` in the second line and the `>>` in the line preceding `endobj` denote
that it is a dictionary object. Dictionaries map Names to other objects.

Names are the strings preceded by '/', valid Names do not have to start with a
capital letter, they can be any ascii characters, # and two characters can
escape non-printable ascii characters, described on page 57.

`3 0 obj` means what follows here is the third object, but the name Type
(represented here by `/Type`) is mapped to an indirect object reference:
`0 obj` vs `0 R`. (Page 64 of Adobe Reference)

The structure of this data, in python/dict form, is thus:
third_obj = {
  pdf_name('Type'): pdf_name('Page'),
  pdf_name('Parent'): iobj_ref(1),
  pdf_name('Resources'): iobj_ref(2),
  pdf_name('Contents'): iobj_ref(4),
}

`collections.OrderedDict` is used because ultimately to test the accuracy of
the documents created, order of the fields matters even though it probably
doesn't in the Adobe Specification.

Some additional notes:

Streams are of the form:

<pre>
4 0 obj
<</Filter /ASCIIHexDecode /Length 22>>
stream
68656c6c6f20776f726c64
endstream
endobj
</pre>

In this case, the ASCIIHexDecode filter is used because
"68656c6c6f20776f726c64" is "hello world" in ascii, and 22 is the length of
that string.

As of this writing, I am not sure how length is actually calculated, so this
remains something to be looked into.

"""
from collections import OrderedDict


def create_name(name):
    if name.startswith("/"):
        name = name[1:]
    return "".join(["/", name[0].upper(), name[1:]])


def clear_empty_fields(d):
    return OrderedDict((k, v) for k, v in d.items() if v)


def create_dictionary_string(
    dict_,
    open_dict="<<",
    close_dict=">>",
    field_join="\n",
    key_value_join=" ",
    has_empty_fields=False,
):
    """format ordered dictionary as PDF dictionary

    @param dict_: dictionary of values to render
    @param open: string to open PDF dictionary
    @param close: string to close PDF dictionary
    @param field_join: string to join fields with
    @param key_value_join: string to join key to value with
    @param has_empty_fields: whether or not to clear_empty_fields first.
    """
    if has_empty_fields:
        dict_ = clear_empty_fields(dict_)

    return "".join(
        [
            open_dict,
            field_join.join([key_value_join.join(f) for f in dict_.items()]),
            close_dict,
        ]
    )


def create_list_string(list_):
    """format list of strings as PDF array"""
    return "[" + " ".join(list_) + "]"


def iobj_ref(n):
    """format an indirect PDF Object reference from its id number"""
    return str(n) + " 0 R"


def create_stream(stream):
    if type(stream) in (bytearray, bytes):
        stream = str(stream, "latin-1")
    return "\n".join(["stream", stream, "endstream"])


if __name__ == "__main__":
    print(create_name("/ok"))
    print(create_name("ok"))
    print(create_name("Ok"))
    print(create_name("/Ok"))
