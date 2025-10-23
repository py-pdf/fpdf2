"""
Classes & functions that represent core elements of the PDF syntax

Most of what happens in a PDF happens in objects, which are formatted like so:
```
3 0 obj
<</Type /Page
/Parent 1 0 R
/Resources 2 0 R
/Contents 4 0 R>>
endobj
```

The first line says that this is the third object in the structure of the document.

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

Names are the strings preceded by `/`, valid Names do not have to start with a
capital letter, they can be any ascii characters, # and two characters can
escape non-printable ascii characters, described on page 57.

`3 0 obj` means what follows here is the third object, but the name Type
(represented here by `/Type`) is mapped to an indirect object reference:
`0 obj` vs `0 R`.

The structure of this data, in python/dict form, is thus:
```
third_obj = {
  '/Type': '/Page'),
  '/Parent': iobj_ref(1),
  '/Resources': iobj_ref(2),
  '/Contents': iobj_ref(4),
}
```

Content streams are of the form:
```
4 0 obj
<</Filter /ASCIIHexDecode /Length 22>>
stream
68656c6c6f20776f726c64
endstream
endobj
```

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import re, zlib
from abc import ABC
from binascii import hexlify
from codecs import BOM_UTF16_BE
from datetime import datetime, timezone


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


def create_stream(stream, encryption_handler=None, obj_id=None):
    if isinstance(stream, (bytearray, bytes)):
        stream = str(stream, "latin-1")
    if encryption_handler:
        encryption_handler.encrypt(stream, obj_id)
    return "\n".join(["stream", stream, "endstream"])


def wrap_in_local_context(draw_commands):
    """
    Wrap a series of draw commands (list of strings) in a local context marker, so that changes to
    draw style only apply to these commands.
    """
    return ["q"] + draw_commands + ["Q"]


class Raw(str):
    """str subclass signifying raw data to be directly emitted to PDF without transformation."""


class Name(str):
    """str subclass signifying a PDF name, which are emitted differently than normal strings."""

    NAME_ESC = re.compile(
        b"[^" + bytes(v for v in range(33, 127) if v not in b"()<>[]{}/%#\\") + b"]"
    )

    def serialize(self, _security_handler=None, _obj_id=None) -> str:
        escaped = self.NAME_ESC.sub(
            lambda m: b"#%02X" % m[0][0], self.encode()
        ).decode()
        return f"/{escaped}"


class PDFObject:
    # Main features of this class:
    # * delay ID assignment
    # * implement serializing
    # Note: several child classes use __slots__ to save up some memory

    def __init__(self):
        self._id = None

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

    def serialize(self, obj_dict=None, _security_handler=None):
        "Serialize the PDF object as an obj<</>>endobj text block"
        output = []
        output.append(f"{self.id} 0 obj")
        output.append("<<")
        if not obj_dict:
            obj_dict = self._build_obj_dict(_security_handler)
        output.append(create_dictionary_string(obj_dict, open_dict="", close_dict=""))
        output.append(">>")
        content_stream = self.content_stream()
        if content_stream:
            output.append(create_stream(content_stream))
        output.append("endobj")
        return "\n".join(output)

    # pylint: disable=no-self-use
    def content_stream(self):
        "Subclasses can override this method to indicate the presence of a content stream"
        return b""

    def _build_obj_dict(self, security_handler=None):
        """
        Build the PDF Object associative map to serialize,
        based on this class instance properties.
        The property names are converted from snake_case to CamelCase,
        and prefixed with a slash character "/".
        """
        return build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=security_handler,
            _obj_id=self.id,
        )


class PDFContentStream(PDFObject):
    # Passed to zlib.compress() - In range 0-9 - Default is currently equivalent to 6:
    _COMPRESSION_LEVEL = -1

    def __init__(self, contents, compress=False):
        super().__init__()
        self._contents = (
            zlib.compress(contents, level=self._COMPRESSION_LEVEL)
            if compress
            else contents
        )
        self.filter = Name("FlateDecode") if compress else None
        self.length = len(self._contents)

    # method override
    def content_stream(self):
        return self._contents

    # method override
    def serialize(self, obj_dict=None, _security_handler=None):
        if _security_handler:
            assert not obj_dict
            if not isinstance(self._contents, (bytearray, bytes)):
                self._contents = self._contents.encode("latin-1")
            self._contents = _security_handler.encrypt(self._contents, self.id)
            self.length = len(self._contents)
        return super().serialize(obj_dict, _security_handler)


def build_obj_dict(key_values, _security_handler=None, _obj_id=None):
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
        # pylint: disable=redefined-loop-name
        if hasattr(value, "value"):  # e.g. Enum subclass
            value = value.value
        if isinstance(value, PDFObject):  # indirect object reference
            value = value.ref
        elif hasattr(value, "serialize"):
            # e.g. PDFArray, PDFString, Name, Destination, Action...
            value = value.serialize(
                _security_handler=_security_handler, _obj_id=_obj_id
            )
        elif isinstance(value, bool):
            value = str(value).lower()
        obj_dict[f"/{camel_case(key)}"] = value
    return obj_dict


def camel_case(snake_case):
    return "".join(x for x in snake_case.title() if x != "_")


class PDFString(str):
    USE_HEX_ENCODING = True
    """
    Setting this to False can reduce the encoded strings size,
    but then there can be a risk of badly encoding some unicode strings - cf. issue #458
    """

    def __new__(cls, content, encrypt=False):
        """
        Args:
            content (str): text
            encrypt (bool): if document encryption is enabled, should this string be encrypted?
        """
        self = super().__new__(cls, content)
        self.encrypt = encrypt
        return self

    def serialize(self, _security_handler=None, _obj_id=None):
        if _security_handler and self.encrypt:
            assert _obj_id
            return _security_handler.encrypt_string(self, _obj_id)
        try:
            self.encode("ascii")
            # => this string only contains ASCII characters, no need for special encoding:
            return f"({self})"
        except UnicodeEncodeError:
            pass
        if self.USE_HEX_ENCODING:
            # Using the "Hexadecimal String" format defined in the PDF spec:
            hex_str = hexlify(BOM_UTF16_BE + self.encode("utf-16-be")).decode("latin-1")
            return f"<{hex_str}>"
        return f'({self.encode("UTF-16").decode("latin-1")})'


class PDFDate:
    def __init__(self, date: datetime, with_tz=False, encrypt=False):
        """
        Args:
            date (datetime): self-explanatory
            with_tz (bool): should the timezone be encoded in included in the date?
            encrypt (bool): if document encryption is enabled, should this string be encrypted?
        """
        self.date = date
        self.with_tz = with_tz
        self.encrypt = encrypt

    def __repr__(self):
        return f"PDFDate({self.date}, with_tz={self.with_tz}, encrypt={self.encrypt})"

    def serialize(self, _security_handler=None, _obj_id=None):
        if self.with_tz:
            assert self.date.tzinfo
            if self.date.tzinfo == timezone.utc:
                out_str = f"D:{self.date:%Y%m%d%H%M%SZ}"
            else:
                out_str = f"D:{self.date:%Y%m%d%H%M%S%z}"
                out_str = out_str[:-2] + "'" + out_str[-2:] + "'"
        else:
            out_str = f"D:{self.date:%Y%m%d%H%M%S}"
        if _security_handler and self.encrypt:
            assert _obj_id
            return _security_handler.encrypt_string(out_str, _obj_id)
        return f"({out_str})"


class PDFArray(list):
    def serialize(self, _security_handler=None, _obj_id=None):
        if all(isinstance(elem, str) for elem in self):
            serialized_elems = " ".join(self)
        elif all(isinstance(elem, (int, float)) for elem in self):
            serialized_elems = " ".join(str(elem) for elem in self)
        else:
            serialized_chunks = []
            for elem in self:
                if isinstance(elem, PDFObject):
                    serialized_chunks.append(elem.ref)
                elif hasattr(elem, "serialize"):
                    serialized_chunks.append(
                        elem.serialize(
                            _security_handler=_security_handler, _obj_id=_obj_id
                        )
                    )
                elif isinstance(elem, bool):
                    serialized_chunks.append(str(elem).lower())
                elif isinstance(elem, (int, float)):
                    serialized_chunks.append(str(elem))
                else:
                    serialized_chunks.append(str(elem))
            serialized_elems = "\n".join(serialized_chunks)
        return f"[{serialized_elems}]"


# cf. section 8.2.1 "Destinations" of the 2006 PDF spec 1.7:
class Destination(ABC):
    def serialize(self, _security_handler=None, _obj_id=None):
        raise NotImplementedError


class DestinationXYZ(Destination):
    def __init__(self, page, top, left=0, zoom="null"):
        self.page_number = page
        self.top = top
        self.left = left
        self.zoom = zoom
        self.page_ref = None

    def __eq__(self, dest):
        return (
            self.page_number == dest.page_number
            and self.top == dest.top
            and self.left == dest.left
            and self.zoom == dest.zoom
        )

    def __hash__(self):
        return hash((self.page_number, self.top, self.left, self.zoom))

    def __repr__(self):
        return f'DestinationXYZ(page_number={self.page_number}, top={self.top}, left={self.left}, zoom="{self.zoom}", page_ref={self.page_ref})'

    def serialize(self, _security_handler=None, _obj_id=None):
        left = round(self.left, 2) if isinstance(self.left, float) else self.left
        top = round(self.top, 2) if isinstance(self.top, float) else self.top
        assert self.page_ref
        return f"[{self.page_ref} /XYZ {left} {top} {self.zoom}]"

    def replace(self, page=None, top=None, left=None, zoom=None):
        assert (
            not self.page_ref
        ), "DestinationXYZ should not be copied after serialization"
        return DestinationXYZ(
            page=self.page_number if page is None else page,
            top=self.top if top is None else top,
            left=self.left if left is None else left,
            zoom=self.zoom if zoom is None else zoom,
        )
