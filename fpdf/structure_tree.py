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

from .util.syntax import create_dictionary_string as pdf_d, iobj_ref as pdf_ref


# pylint: disable=inherit-non-class,unsubscriptable-object
class MarkedContent(NamedTuple):
    page_object_id: int  # refers to the first page displaying this marked content
    struct_parents_id: int
    struct_type: str
    mcid: Optional[int] = None
    title: Optional[str] = None
    alt_text: Optional[str] = None


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
        return pdf_ref(self.id)

    def serialize(self, fpdf=None, obj_dict=None):
        output = []
        if fpdf:
            # pylint: disable=protected-access
            appender = fpdf._out
            assert (
                fpdf._newobj() == self.id
            ), "Something went wrong in StructTree object IDs assignement"
        else:
            appender = output.append
            appender(f"{self.id} 0 obj")
        appender("<<")
        if not obj_dict:
            obj_dict = self._build_obj_dict()
        appender(pdf_d(obj_dict, open_dict="", close_dict=""))
        appender(">>")
        appender("endobj")
        return "\n".join(output)

    def _build_obj_dict(self):
        """
        Build the PDF Object associative map to serialize,
        based on this class instance properties.
        The property names are converted to CamelCase,
        and prefixed with a slash character "/".
        """
        obj_dict = {}
        for key in dir(self):
            value = getattr(self, key)
            if (
                callable(value)
                or key.startswith("_")
                or key in ("id", "ref")
                or value is None
            ):
                continue
            if isinstance(value, PDFObject):  # indirect object reference
                value = value.ref
            elif hasattr(value, "serialize"):  # e.g. PDFArray & PDFString
                value = value.serialize()
            obj_dict[f"/{camel_case(key)}"] = value
        return obj_dict


def camel_case(property_name):
    return "".join(x for x in property_name.title() if x != "_")


class PDFString(str):
    def serialize(self):
        return f"({self})"


class PDFArray(list):
    def serialize(self):
        if all(isinstance(elem, PDFObject) for elem in self):
            serialized_elems = "\n".join(elem.ref for elem in self)
        elif all(isinstance(elem, int) for elem in self):
            serialized_elems = " ".join(map(str, self))
        else:
            raise NotImplementedError(f"PDFArray.serialize with self={self}")
        return f"[{serialized_elems}]"


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
    def __init__(self, marked_contents=()):
        """
        Args:
            marked_contents (tuple): list of MarkedContent
        """
        self.struct_tree_root = StructTreeRoot()
        self.doc_struct_elem = StructElem(
            struct_type="/Document", parent=self.struct_tree_root, kids=[]
        )
        self.struct_tree_root.k.append(self.doc_struct_elem)
        for marked_content in marked_contents:
            self.add_marked_content(marked_content)

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
        self.doc_struct_elem.k.append(struct_elem)
        self.struct_tree_root.parent_tree.nums[marked_content.struct_parents_id].append(
            struct_elem
        )

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
