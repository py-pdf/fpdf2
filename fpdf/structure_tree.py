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
from typing import NamedTuple, List, Optional

from .util.syntax import create_dictionary_string as pdf_d, iobj_ref as pdf_ref


# pylint: disable=inherit-non-class,unsubscriptable-object
class MarkedContent(NamedTuple):
    page_object_id: int  # refers to the first page displaying this marked content
    struct_parents_id: int
    mcid: int
    title: Optional[str] = None
    alt_text: Optional[str] = None


class PDFObject:
    """
    Main features of this class:
    * delay ID assignement
    * implement serializing
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
            obj_dict = {}
            for key, value in self.__dict__.items():
                if not key.startswith("_") and value is not None:
                    if isinstance(value, PDFObject):  # indirect object reference
                        value = value.ref
                    elif isinstance(value, list):  # e.g. K (children/kids)
                        if all(
                            isinstance(elem, PDFObject) for elem in value
                        ):  # e.g. List[ObjectReferenceDictionary]
                            serialized_elems = "\n".join(elem.ref for elem in value)
                        elif all(
                            isinstance(elem, int) for elem in value
                        ):  # e.g. List[int]
                            serialized_elems = " ".join(map(str, value))
                        else:
                            raise NotImplementedError
                        value = f"[{serialized_elems}]"
                    elif hasattr(value, "serialize"):  # e.g. ObjectReferenceDictionary
                        value = value.serialize()
                    elif key in ("T", "Alt"):
                        value = f"({value})"
                    obj_dict[f"/{key}"] = value
        appender(pdf_d(obj_dict, open_dict="", close_dict=""))
        appender(">>")
        appender("endobj")
        return "\n".join(output)


class ObjectReferenceDictionary:
    def __init__(self, Pg: PDFObject, Obj: PDFObject):
        self.Pg = Pg  # page on which the object is rendered
        self.Obj = Obj  # the referenced object

    def serialize(self):
        return pdf_d(
            {
                "/Type": "/OBJR",
                "/Pg": self.Pg.ref,
                "/Obj": self.Obj.ref,
            }
        )


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Nums = defaultdict(list)  # {struct_parent_id -> struct_elems}

    def serialize(self, fpdf=None, obj_dict=None):
        newline = "\n"
        serialized_nums = "\n".join(
            f"{struct_parent_id} [{newline.join(struct_elem.ref for struct_elem in struct_elems)}]"
            for struct_parent_id, struct_elems in self.Nums.items()
        )
        return super().serialize(fpdf, {"/Nums": f"[{serialized_nums}]"})


class StructTreeRoot(PDFObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Type = "/StructTreeRoot"
        # A number tree used in finding the structure elements to which content items belong:
        self.ParentTree = NumberTree()
        # The immediate child or children of the structure tree root in the structure hierarchy:
        self.K = []


class StructElem(PDFObject):
    def __init__(
        self,
        S: str,
        P: PDFObject,
        K: List[int],
        Pg: PDFObject = None,
        T: str = None,
        Alt: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.Type = "/StructElem"
        self.S = S  # The structure type, a name object identifying the nature of the structure element
        self.P = P  # The structure element that is the immediate parent of this one in the structure hierarchy
        self.K = K  # The children of this structure element
        self.Pg = Pg  # A page object on which some or all of the content items designated by the K entry are rendered.
        self.T = T  # The title of the structure element, a text string representing it in human-readable form
        self.Alt = Alt  # An alternate description of the structure element and its children in human-readable form


class StructureTreeBuilder:
    def __init__(self, marked_contents=()):
        """
        Args:
            marked_contents (tuple): list of MarkedContent
        """
        self.struct_tree_root = StructTreeRoot()
        self.doc_struct_elem = StructElem(S="/Document", P=self.struct_tree_root, K=[])
        self.struct_tree_root.K.append(self.doc_struct_elem)
        for marked_content in marked_contents:
            self.add_marked_content(marked_content)

    def add_marked_content(self, marked_content):
        page = PDFObject(marked_content.page_object_id)
        struct_elem = StructElem(
            S="/Figure",
            P=self.doc_struct_elem,
            K=[marked_content.mcid],
            Pg=page,
            T=marked_content.title,
            Alt=marked_content.alt_text,
        )
        self.doc_struct_elem.K.append(struct_elem)
        self.struct_tree_root.ParentTree.Nums[marked_content.struct_parents_id].append(
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
        output.append(self.struct_tree_root.ParentTree.serialize(fpdf))
        for struct_elem in self.doc_struct_elem.K:
            output.append(struct_elem.serialize(fpdf))
        return "\n".join(output)

    def assign_ids(self, n):
        self.struct_tree_root.id = n
        n += 1
        self.doc_struct_elem.id = n
        n += 1
        self.struct_tree_root.ParentTree.id = n
        n += 1
        for struct_elem in self.doc_struct_elem.K:
            struct_elem.id = n
            n += 1
        return n
