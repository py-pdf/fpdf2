"""PDF Syntax Helpers

Functions in this module take variable input and produce PDF Syntax features
as they are described in the Adobe PDF Reference Manual, found here:
http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

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
  '/Type': '/Page'),
  '/Parent': iobj_ref(1),
  '/Resources': iobj_ref(2),
  '/Contents': iobj_ref(4),
}

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
from abc import ABC
import re

from .util import object_id_for_page


def clear_empty_fields(d):
    return {k: v for k, v in d.items() if v}


def create_dictionary_string(
    dict_,
    open_dict="<<",
    close_dict=">>",
    field_join="\n",
    key_value_join=" ",
    has_empty_fields=False,
):
    """format dictionary as PDF dictionary

    @param dict_: dictionary of values to render
    @param open_dict: string to open PDF dictionary
    @param close_dict: string to close PDF dictionary
    @param field_join: string to join fields with
    @param key_value_join: string to join key to value with
    @param has_empty_fields: whether or not to clear_empty_fields first.
    """
    if has_empty_fields:
        dict_ = clear_empty_fields(dict_)

    return "".join(
        [
            open_dict,
            field_join.join(key_value_join.join((k, str(v))) for k, v in dict_.items()),
            close_dict,
        ]
    )


def create_list_string(list_):
    """format list of strings as PDF array"""
    return f"[{' '.join(list_)}]"


def iobj_ref(n):
    """format an indirect PDF Object reference from its id number"""
    return f"{n} 0 R"


def create_stream(stream):
    if isinstance(stream, (bytearray, bytes)):
        stream = str(stream, "latin-1")
    return "\n".join(["stream", stream, "endstream"])


class Raw(str):
    """str subclass signifying raw data to be directly emitted to PDF without transformation."""


class Name(str):
    """str subclass signifying a PDF name, which are emitted differently than normal strings."""

    NAME_ESC = re.compile(
        b"[^" + bytes(v for v in range(33, 127) if v not in b"()<>[]{}/%#\\") + b"]"
    )

    def pdf_repr(self) -> str:
        escaped = self.NAME_ESC.sub(
            lambda m: b"#%02X" % m[0][0], self.encode()
        ).decode()
        return f"/{escaped}"


class PDFObject:
    """
    Main features of this class:
    * delay ID assignement
    * implement serializing

    To ensure consistency on how the serialize() method operates,
    child classes must define a __slots__ attribute.
    """

    # pylint: disable=redefined-builtin
    def __init__(self, id=None):
        self._id = id

    @property
    def id(self):
        if self._id is None:
            raise AttributeError(
                f"{self.__class__.__name__} has not been assigned an ID yet"
            )
        return self._id

    @id.setter
    def id(self, n):
        self._id = n

    @property
    def ref(self):
        return iobj_ref(self.id)

    def serialize(self, fpdf=None, obj_dict=None):
        output = []
        if fpdf:
            # pylint: disable=protected-access
            appender = fpdf._out
            assert (
                fpdf._newobj() == self.id
            ), "Something went wrong in StructTree object IDs assignment"
        else:
            appender = output.append
            appender(f"{self.id} 0 obj")
        appender("<<")
        if not obj_dict:
            obj_dict = self._build_obj_dict()
        appender(create_dictionary_string(obj_dict, open_dict="", close_dict=""))
        appender(">>")
        appender("endobj")
        return "\n".join(output)

    def _build_obj_dict(self):
        """
        Build the PDF Object associative map to serialize,
        based on this class instance properties.
        The property names are converted from snake_case to CamelCase,
        and prefixed with a slash character "/".
        """
        return build_obj_dict({key: getattr(self, key) for key in dir(self)})


def build_obj_dict(key_values):
    """
    Build the PDF Object associative map to serialize, based on a key-values dict.
    The property names are converted from snake_case to CamelCase,
    and prefixed with a slash character "/".
    """
    obj_dict = {}
    for key, value in key_values.items():
        if (
            callable(value)
            or key.startswith("_")
            or key in ("id", "ref")
            or value is None
        ):
            continue
        if hasattr(value, "value"):  # e.g. Enum subclass
            value = value.value
        if isinstance(value, PDFObject):  # indirect object reference
            value = value.ref
        elif hasattr(value, "pdf_repr"):  # e.g. Name
            value = value.pdf_repr()
        elif hasattr(value, "serialize"):  # e.g. PDFArray & PDFString
            value = value.serialize()
        elif isinstance(value, bool):
            value = str(value).lower()
        obj_dict[f"/{camel_case(key)}"] = value
    return obj_dict


def camel_case(snake_case):
    return "".join(x for x in snake_case.title() if x != "_")


class PDFString(str):
    def serialize(self):
        return f'({self.encode("UTF-16").decode("latin-1")})'


class PDFArray(list):
    def serialize(self):
        if all(isinstance(elem, PDFObject) for elem in self):
            serialized_elems = "\n".join(elem.ref for elem in self)
        elif all(isinstance(elem, int) for elem in self):
            serialized_elems = " ".join(map(str, self))
        else:
            raise NotImplementedError(f"PDFArray.serialize with self={self}")
        return f"[{serialized_elems}]"


# cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
class Destination(ABC):
    def as_str(self, pdf=None):
        raise NotImplementedError


class DestinationXYZ(Destination):
    def __init__(self, page, x=0, y=0, zoom="null", page_as_obj_id=True):
        self.page = page
        self.x = x
        self.y = y
        self.zoom = zoom
        self.page_as_obj_id = page_as_obj_id

    def __repr__(self):
        return f'DestinationXYZ(page={self.page}, x={self.x}, y={self.y}, zoom="{self.zoom}", page_as_obj_id={self.page_as_obj_id})'

    def as_str(self, pdf=None):
        left = self.x * pdf.k if pdf else self.x
        if isinstance(left, float):
            left = round(left, 2)
        top = (pdf.h_pt - self.y * pdf.k) if pdf else self.y
        if isinstance(top, float):
            top = round(top, 2)
        page = (
            iobj_ref(object_id_for_page(self.page))
            if self.page_as_obj_id
            else self.page
        )
        return f"[{page} /XYZ {left} {top} {self.zoom}]"
