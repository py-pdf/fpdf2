from datetime import datetime
from typing import NamedTuple, Optional, Tuple, Union

from .enums import AnnotationFlag, AnnotationName
from .actions import Action


# cf. https://docs.verapdf.org/validation/pdfa-part1/#rule-653-2
DEFAULT_ANNOT_FLAGS = (AnnotationFlag.PRINT,)


class Annotation(NamedTuple):
    type: str
    x: int
    y: int
    width: int
    height: int
    flags: Tuple[AnnotationFlag] = DEFAULT_ANNOT_FLAGS
    contents: str = None
    link: Union[str, int] = None
    action: Optional[Action] = None
    color: Optional[int] = None
    modification_time: Optional[datetime] = None
    title: Optional[str] = None
    quad_points: Optional[tuple] = None
    page: Optional[int] = None
    border_width: int = 0  # PDF readers support: displayed by Acrobat but not Sumatra
    name: Optional[AnnotationName] = None  # for text annotations
    ink_list: Tuple[int] = ()  # for ink annotations
    embedded_file_name: Optional[str] = None
    field_type: Optional[str] = None
    value: Optional[str] = None
