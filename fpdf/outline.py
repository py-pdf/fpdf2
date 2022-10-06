"""
Quoting section 8.2.2 "Document Outline" of the 2006 PDF spec 1.7:
> The document outline consists of a tree-structured hierarchy of outline items (sometimes called bookmarks),
> which serve as a visual table of contents to display the document’s structure to the user.
"""
from typing import NamedTuple, Optional

from .syntax import Destination, PDFObject, PDFString
from .syntax import iobj_ref as pdf_ref
from .structure_tree import StructElem


class OutlineSection(NamedTuple):
    name: str
    level: str
    page_number: int
    dest: Destination
    struct_elem: Optional[StructElem] = None


class OutlineItemDictionary(PDFObject):
    __slots__ = (
        "_id",
        "title",
        "parent",
        "prev",
        "next",
        "first",
        "last",
        "count",
        "dest",
        "struct_elem",
    )

    def __init__(
        self,
        title: str,
        dest: Destination = None,
        struct_elem: StructElem = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = PDFString(title)
        self.parent = None
        self.prev = None
        self.next = None
        self.first = None
        self.last = None
        self.count = 0
        self.dest = dest
        self.struct_elem = struct_elem


class OutlineDictionary(PDFObject):
    __slots__ = ("_id", "type", "first", "last", "count")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "/Outlines"
        self.first = None
        self.last = None
        self.count = 0


def build_outline_objs(sections, page_objs):
    """
    Build PDF objects constitutive of the documents outline,
    and yield them one by one, starting with the outline dictionary
    """
    outline = OutlineDictionary()
    yield outline
    outline_items = []
    last_outline_item_per_level = {}
    for section in sections:
        section.dest.page_ref = pdf_ref(page_objs[section.dest.page_number - 1].id)
        outline_item = OutlineItemDictionary(
            title=section.name,
            dest=section.dest,
            struct_elem=section.struct_elem,
        )
        yield outline_item
        if section.level in last_outline_item_per_level:
            last_outline_item_at_level = last_outline_item_per_level[section.level]
            last_outline_item_at_level.next = outline_item
            outline_item.prev = last_outline_item_at_level
        if section.level - 1 in last_outline_item_per_level:
            parent_outline_item = last_outline_item_per_level[section.level - 1]
        else:
            parent_outline_item = outline
        outline_item.parent = parent_outline_item
        if parent_outline_item.first is None:
            parent_outline_item.first = outline_item
        parent_outline_item.last = outline_item
        parent_outline_item.count += 1
        outline_items.append(outline_item)
        last_outline_item_per_level[section.level] = outline_item
        last_outline_item_per_level = {
            level: oitem
            for level, oitem in last_outline_item_per_level.items()
            if level <= section.level
        }
    return [outline] + outline_items
