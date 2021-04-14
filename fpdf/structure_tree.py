"""
Quoting the PDF spec:
> PDF’s logical _structure facilities_ provide a mechanism for incorporating
> structural information about a document’s content into a PDF file.

> The logical structure of a document is described by a hierarchy of objects called
> the _structure hierarchy_ or _structure tree_.
> At the root of the hierarchy is a dictionary object called the _structure tree root_,
> located by means of the **StructTreeRoot** entry in the document catalog.
"""
from collections import defaultdict
from typing import NamedTuple, List, Optional, Union

from .syntax import PDFObject, PDFString, PDFArray


# pylint: disable=inherit-non-class,unsubscriptable-object
class MarkedContent(NamedTuple):
    page_object_id: int  # refers to the first page displaying this marked content
    struct_parents_id: int
    struct_type: str
    mcid: Optional[int] = None
    title: Optional[str] = None
    alt_text: Optional[str] = None


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

    __slots__ = ("_id", "nums")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nums = defaultdict(list)  # {struct_parent_id -> struct_elems}

    def serialize(self, fpdf=None, obj_dict=None):
        newline = "\n"
        serialized_nums = "\n".join(
            f"{struct_parent_id} [{newline.join(struct_elem.ref for struct_elem in struct_elems)}]"
            for struct_parent_id, struct_elems in self.nums.items()
        )
        return super().serialize(fpdf, {"/Nums": f"[{serialized_nums}]"})


class StructTreeRoot(PDFObject):
    __slots__ = ("_id", "type", "parent_tree", "k")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "/StructTreeRoot"
        # A number tree used in finding the structure elements to which content items belong:
        self.parent_tree = NumberTree()
        # The immediate child or children of the structure tree root in the structure hierarchy:
        self.k = PDFArray()


class StructElem(PDFObject):
    # The main reason to use __slots__ in PDFObject child classes is to save up some memory
    # when very many instances of this class are created.
    __slots__ = ("_id", "type", "s", "p", "k", "pg", "t", "alt")

    def __init__(
        self,
        struct_type: str,
        parent: PDFObject,
        kids: Union[List[int], List["StructElem"]],
        page: PDFObject = None,
        title: str = None,
        alt: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.type = "/StructElem"
        self.s = (
            struct_type  # a name object identifying the nature of the structure element
        )
        self.p = parent  # The structure element that is the immediate parent of this one in the structure hierarchy
        self.k = PDFArray(kids)  # The children of this structure element
        self.pg = page  # A page object on which some or all of the content items designated by the K entry are rendered
        self.t = (
            None if title is None else PDFString(title)
        )  # a text string representing it in human-readable form
        self.alt = (
            None if alt is None else PDFString(alt)
        )  # An alternate description of the structure element in human-readable form


class StructureTreeBuilder:
    def __init__(self):
        """
        Args:
            marked_contents (tuple): list of MarkedContent
        """
        self.struct_tree_root = StructTreeRoot()
        self.doc_struct_elem = StructElem(
            struct_type="/Document", parent=self.struct_tree_root, kids=[]
        )
        self.struct_tree_root.k.append(self.doc_struct_elem)
        self.struct_elem_per_mc = {}

    def add_marked_content(self, marked_content):
        page = PDFObject(marked_content.page_object_id)
        struct_elem = StructElem(
            struct_type=marked_content.struct_type,
            parent=self.doc_struct_elem,
            kids=[] if marked_content.mcid is None else [marked_content.mcid],
            page=page,
            title=marked_content.title,
            alt=marked_content.alt_text,
        )
        self.struct_elem_per_mc[marked_content] = struct_elem
        self.doc_struct_elem.k.append(struct_elem)
        self.struct_tree_root.parent_tree.nums[marked_content.struct_parents_id].append(
            struct_elem
        )

    def next_mcid_for_page(self, page_object_id):
        return sum(
            1 for mc in self.struct_elem_per_mc if mc.page_object_id == page_object_id
        )

    def empty(self):
        return not self.struct_elem_per_mc

    def serialize(self, first_object_id=1, fpdf=None):
        """
        Assign object IDs & output the whole hierarchy tree serialized
        as a multi-lines string in PDF syntax, ready to be embedded.

        Objects ID assignement will start with the provided first ID,
        that will be assigned to the StructTreeRoot.
        Apart from that, assignement is made in an arbitrary order.
        All PDF objects must have assigned IDs before proceeding to output
        generation though, as they have many references to each others.

        If a FPDF instance provided, its `_newobj` & `_out` methods will be called
        and this method output will be meaningless.
        """
        self.assign_ids(first_object_id)
        output = []
        output.append(self.struct_tree_root.serialize(fpdf))
        output.append(self.doc_struct_elem.serialize(fpdf))
        output.append(self.struct_tree_root.parent_tree.serialize(fpdf))
        for struct_elem in self.doc_struct_elem.k:
            output.append(struct_elem.serialize(fpdf))
        return "\n".join(output)

    def assign_ids(self, n):
        self.struct_tree_root.id = n
        n += 1
        self.doc_struct_elem.id = n
        n += 1
        self.struct_tree_root.parent_tree.id = n
        n += 1
        for struct_elem in self.doc_struct_elem.k:
            struct_elem.id = n
            n += 1
        return n
