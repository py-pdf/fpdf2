"""
Quoting the PDF spec:
> PDF’s logical _structure facilities_ provide a mechanism for incorporating
> structural information about a document’s content into a PDF file.

> The logical structure of a document is described by a hierarchy of objects called
> the _structure hierarchy_ or _structure tree_.
> At the root of the hierarchy is a dictionary object called the _structure tree root_,
> located by means of the **StructTreeRoot** entry in the document catalog.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html>
"""

from collections import defaultdict
from typing import List, Union

from .syntax import PDFObject, PDFString, PDFArray


class NumberTree(PDFObject):
    """A number tree is similar to a name tree, except that its keys are integers
    instead of strings and are sorted in ascending numerical order.

    A name tree serves a similar purpose to a dictionary—associating keys and
    values—but by different means.

    The values associated with the keys may be objects of any type. Stream objects
    are required to be specified by indirect object references. It is recommended,
    though not required, that dictionary, array, and string objects be specified by
    indirect object references, and other PDF objects (nulls, numbers, booleans,
    and names) be specified as direct objects
    """

    __slots__ = ("_id", "nums")  # RAM usage optimization

    def __init__(self):
        super().__init__()
        self.nums = defaultdict(list)  # {struct_parent_id -> struct_elems}

    def serialize(self, obj_dict=None, _security_handler=None):
        newline = "\n"
        serialized_nums = "\n".join(
            f"{struct_parent_id} [{newline.join(struct_elem.ref for struct_elem in struct_elems)}]"
            for struct_parent_id, struct_elems in self.nums.items()
        )
        return super().serialize({"/Nums": f"[{serialized_nums}]"})


class StructTreeRoot(PDFObject):
    __slots__ = ("_id", "type", "parent_tree", "k")  # RAM usage optimization

    def __init__(self):
        super().__init__()
        self.type = "/StructTreeRoot"
        # A number tree used in finding the structure elements to which content items belong:
        self.parent_tree = NumberTree()
        # The immediate child or children of the structure tree root in the structure hierarchy:
        self.k = PDFArray()


class StructElem(PDFObject):
    __slots__ = (  # RAM usage optimization
        "_id",
        "type",
        "s",
        "p",
        "k",
        "t",
        "alt",
        "pg",
        "_page_number",
    )

    def __init__(
        self,
        struct_type: str,
        parent: PDFObject,
        kids: Union[List[int], List["StructElem"]],
        page_number: int = None,
        title: str = None,
        alt: str = None,
    ):
        super().__init__()
        self.type = "/StructElem"
        # A name object identifying the nature of the structure element:
        self.s = struct_type
        self.p = parent  # The structure element that is the immediate parent of this one in the structure hierarchy
        self.k = PDFArray(kids)  # The children of this structure element
        # a text string representing it in human-readable form:
        self.t = None if title is None else PDFString(title)
        # An alternate description of the structure element in human-readable form:
        self.alt = None if alt is None else PDFString(alt)
        self.pg = None  # A page object on which some or all of the content items designated by the K entry are rendered
        self._page_number = page_number  # private so that it does not get serialized

    def page_number(self):
        return self._page_number


class StructureTreeBuilder:
    def __init__(self):
        self.struct_tree_root = StructTreeRoot()
        self.doc_struct_elem = StructElem(
            struct_type="/Document", parent=self.struct_tree_root, kids=[]
        )
        self.struct_tree_root.k.append(self.doc_struct_elem)
        self.spid_per_page_number = {}  # {page_number -> StructParent(s) ID}

    def add_marked_content(
        self,
        page_number: int,
        struct_type: str,
        mcid: int = None,
        title: str = None,
        alt_text: str = None,
    ):
        struct_parents_id = self.spid_per_page_number.get(page_number)
        if struct_parents_id is None:
            struct_parents_id = len(self.spid_per_page_number)
            self.spid_per_page_number[page_number] = struct_parents_id
        struct_elem = StructElem(
            struct_type=struct_type,
            parent=self.doc_struct_elem,
            kids=[] if mcid is None else [mcid],
            page_number=page_number,
            title=title,
            alt=alt_text,
        )
        self.doc_struct_elem.k.append(struct_elem)
        self.struct_tree_root.parent_tree.nums[struct_parents_id].append(struct_elem)
        return struct_elem, struct_parents_id

    def next_mcid_for_page(self, page_number):
        return sum(
            1
            for struct_elem in self.doc_struct_elem.k
            if struct_elem.page_number() == page_number
            and struct_elem.k  # ensure it has a mcid set
        )

    def empty(self):
        return not self.doc_struct_elem.k

    def __iter__(self):
        "Iterate all PDF objects in the tree, starting with the tree root"
        yield self.struct_tree_root
        yield self.doc_struct_elem
        yield self.struct_tree_root.parent_tree
        yield from self.doc_struct_elem.k
