"""
Usage documentation at: <https://py-pdf.github.io/fpdf2/Annotations.html>
"""

import hashlib
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .actions import Action
from .enums import (
    AnnotationFlag,
    AnnotationName,
    AssociatedFileRelationship,
    FileAttachmentAnnotationName,
)
from .syntax import (
    Destination,
    Name,
    PDFContentStream,
    PDFDate,
    PDFObject,
    PDFString,
    build_obj_dict,
    create_dictionary_string as pdf_dict,
    create_list_string as pdf_list,
    iobj_ref as pdf_ref,
)

if TYPE_CHECKING:
    from .encryption import StandardSecurityHandler

# cf. https://docs.verapdf.org/validation/pdfa-part1/#rule-653-2
DEFAULT_ANNOT_FLAGS = (AnnotationFlag.PRINT,)


class AnnotationMixin:
    def __init__(
        self,
        subtype: str,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: tuple[AnnotationFlag | str, ...] = DEFAULT_ANNOT_FLAGS,
        contents: Optional[str] = None,
        dest: Optional[Destination | PDFString] = None,
        action: Optional[Action] = None,
        color: Optional[tuple[float, float, float]] = None,
        modification_time: Optional[datetime] = None,
        title: Optional[str] = None,
        quad_points: Optional[Sequence[float]] = None,
        border_width: float = 0,  # PDF readers support: displayed by Acrobat but not Sumatra
        name: Union[AnnotationName, FileAttachmentAnnotationName, None] = None,
        ink_list: Optional[tuple[float, ...]] = None,  # for ink annotations
        file_spec: Optional[Union["FileSpec", str]] = None,
        field_type: Optional[str] = None,
        value: Optional[str] = None,
        default_appearance: Optional[str] = None,  # for free text annotations
    ) -> None:
        self.type = Name("Annot")
        self.subtype = Name(subtype)
        self.rect = f"[{x:.2f} {y - height:.2f} {x + width:.2f} {y:.2f}]"
        self.border = f"[0 0 {border_width}]"
        self.f_t = Name(field_type) if field_type else None
        self.v = value
        self.f = sum(tuple(AnnotationFlag.coerce(flag) for flag in flags))
        self.contents = PDFString(contents, encrypt=True) if contents else None
        self.a = action
        self.dest = dest
        self.c = f"[{color[0]} {color[1]} {color[2]}]" if color else None
        self.t = PDFString(title, encrypt=True) if title else None
        self.m = PDFDate(modification_time, encrypt=True) if modification_time else None
        self.quad_points = (
            pdf_list([f"{quad_point:.2f}" for quad_point in quad_points])
            if quad_points
            else None
        )
        self.p = None  # must always be set before calling .serialize()
        self.name = name
        self.ink_list = (
            ("[" + pdf_list([f"{coord:.2f}" for coord in ink_list]) + "]")
            if ink_list
            else None
        )
        self.f_s = file_spec
        self.d_a = default_appearance


class PDFAnnotation(AnnotationMixin, PDFObject):
    "A PDF annotation that get serialized as an obj<</>>endobj block"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


class AnnotationDict(AnnotationMixin):
    "A PDF annotation that get serialized as an inline <<dictionary>>"

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
        "d_a",
    )

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return pdf_dict(obj_dict)

    def __repr__(self) -> str:
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
        creation_date: Optional[datetime] = None,
        modification_date: Optional[datetime] = None,
        mime_type: Optional[str] = None,
        af_relationship: Optional[AssociatedFileRelationship] = None,
        compress: bool = False,
        checksum: bool = False,
    ):
        super().__init__(contents=contents, compress=compress)
        self.type = Name("EmbeddedFile")
        params: dict[str, object] = {"/Size": len(contents)}
        if creation_date:
            params["/CreationDate"] = PDFDate(creation_date, with_tz=True).serialize()
        if modification_date:
            params["/ModDate"] = PDFDate(modification_date, with_tz=True).serialize()
        if checksum:
            file_hash = hashlib.new("md5", usedforsecurity=False)
            file_hash.update(self._contents)
            hash_hex = file_hash.hexdigest()
            params["/CheckSum"] = f"<{hash_hex}>"
        if mime_type:
            self.subtype = Name(mime_type)
        self.params = pdf_dict(params)
        self._basename: str = basename  # private so that it does not get serialized
        self._desc: str = desc  # private so that it does not get serialized
        self._globally_enclosed: bool = True
        self._af_relationship: Optional[AssociatedFileRelationship] = af_relationship
        self._file_spec: Optional[FileSpec] = None

    def globally_enclosed(self) -> bool:
        return self._globally_enclosed

    def set_globally_enclosed(self, value: bool) -> None:
        self._globally_enclosed = value

    def basename(self) -> str:
        return self._basename

    def file_spec(self) -> "FileSpec":
        if not self._file_spec:
            self._file_spec = FileSpec(
                self, self._basename, self._desc, self._af_relationship
            )
        return self._file_spec


class FileSpec(PDFObject):

    def __init__(
        self,
        embedded_file: PDFEmbeddedFile,
        basename: str,
        desc: Optional[str] = None,
        af_relationship: Optional[AssociatedFileRelationship] = None,
    ):
        super().__init__()
        self.type = Name("Filespec")
        self.f = PDFString(basename)
        self.u_f = PDFString(basename)
        if desc:
            self.desc = PDFString(desc)
        if af_relationship:
            self.a_f_relationship = Name(af_relationship.value)
        self._embedded_file = embedded_file

    @property
    def e_f(self) -> str:
        return pdf_dict({"/F": pdf_ref(self._embedded_file.id)})
