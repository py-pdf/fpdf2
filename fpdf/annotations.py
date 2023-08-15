import hashlib
from datetime import datetime
from typing import NamedTuple, Tuple, Union

from .actions import Action
from .enums import AnnotationFlag, AnnotationName, FileAttachmentAnnotationName
from .syntax import (
    build_obj_dict,
    Destination,
    Name,
    PDFContentStream,
    PDFDate,
    PDFObject,
    PDFString,
)
from .syntax import create_dictionary_string as pdf_dict
from .syntax import create_list_string as pdf_list
from .syntax import iobj_ref as pdf_ref


# cf. https://docs.verapdf.org/validation/pdfa-part1/#rule-653-2
DEFAULT_ANNOT_FLAGS = (AnnotationFlag.PRINT,)


class AnnotationMixin:
    def __init__(
        self,
        subtype: str,
        x: int,
        y: int,
        width: int,
        height: int,
        flags: Tuple[AnnotationFlag] = DEFAULT_ANNOT_FLAGS,
        contents: str = None,
        dest: Destination = None,
        action: Action = None,
        color: tuple = None,
        modification_time: datetime = None,
        title: str = None,
        quad_points: tuple = None,
        border_width: int = 0,  # PDF readers support: displayed by Acrobat but not Sumatra
        name: Union[AnnotationName, FileAttachmentAnnotationName] = None,
        ink_list: Tuple[int] = (),  # for ink annotations
        file_spec: str = None,
        field_type: str = None,
        value=None,
    ):
        self.type = Name("Annot")
        self.subtype = Name(subtype)
        self.rect = f"[{x:.2f} {y:.2f} {x + width:.2f} {y - height:.2f}]"
        self.border = f"[0 0 {border_width}]"
        self.f_t = Name(field_type) if field_type else None
        self.v = value
        self.f = sum(flags)
        self.contents = PDFString(contents, encrypt=True) if contents else None
        self.a = action
        self.dest = dest
        self.c = f"[{color[0]} {color[1]} {color[2]}]" if color else None
        self.t = PDFString(title, encrypt=True) if title else None
        self.m = PDFDate(modification_time, encrypt=True) if modification_time else None
        self.quad_points = (
            pdf_list(f"{quad_point:.2f}" for quad_point in quad_points)
            if quad_points
            else None
        )
        self.p = None  # must always be set before calling .serialize()
        self.name = name
        self.ink_list = (
            ("[" + pdf_list(f"{coord:.2f}" for coord in ink_list) + "]")
            if ink_list
            else None
        )
        self.f_s = file_spec


class PDFAnnotation(AnnotationMixin, PDFObject):
    "A PDF annotation that get serialized as an obj<</>>endobj block"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AnnotationDict(AnnotationMixin):
    "A PDF annotation that get serialized as an inline <<dictionnary>>"
    __slots__ = (  # RAM usage optimization
        "type",
        "subtype",
        "rect",
        "border",
        "f_t",
        "v",
        "f",
        "contents",
        "a",
        "dest",
        "c",
        "t",
        "quad_points",
        "p",
        "name",
        "ink_list",
        "f_s",
    )

    def serialize(self, _security_handler=None, _obj_id=None):
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict)

    def __repr__(self):
        keys = [key for key in dir(self) if not key.startswith("__")]
        d = {key: getattr(self, key) for key in keys}
        d = {key: value for key, value in d.items() if not callable(value)}
        return f"AnnotationDict(**{d})"


class PDFEmbeddedFile(PDFContentStream):
    def __init__(
        self,
        basename: str,
        contents: bytes,
        desc: str = "",
        creation_date: datetime = None,
        modification_date: datetime = None,
        compress: bool = False,
        checksum: bool = False,
    ):
        super().__init__(contents=contents, compress=compress)
        self.type = Name("EmbeddedFile")
        params = {"/Size": len(contents)}
        if creation_date:
            params["/CreationDate"] = PDFDate(creation_date, with_tz=True).serialize()
        if modification_date:
            params["/ModDate"] = PDFDate(modification_date, with_tz=True).serialize()
        if checksum:
            file_hash = hashlib.new("md5", usedforsecurity=False)
            file_hash.update(self._contents)
            hash_hex = file_hash.hexdigest()
            params["/CheckSum"] = f"<{hash_hex}>"
        self.params = pdf_dict(params)
        self._basename = basename  # private so that it does not get serialized
        self._desc = desc  # private so that it does not get serialized
        self._globally_enclosed = True

    def globally_enclosed(self):
        return self._globally_enclosed

    def set_globally_enclosed(self, value):
        self._globally_enclosed = value

    def basename(self):
        return self._basename

    def file_spec(self):
        return FileSpec(self, self._basename, self._desc)


class FileSpec(NamedTuple):
    embedded_file: PDFEmbeddedFile
    basename: str
    desc: str

    def serialize(self, _security_handler=None, _obj_id=None):
        obj_dict = {
            "/Type": "/Filespec",
            "/F": PDFString(self.basename).serialize(),
            "/EF": pdf_dict({"/F": pdf_ref(self.embedded_file.id)}),
        }
        if self.desc:
            obj_dict["/Desc"] = PDFString(self.desc).serialize()
        return pdf_dict(obj_dict, field_join=" ")
