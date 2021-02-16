from fpdf.structure_tree import MarkedContent, PDFObject, StructureTreeBuilder


def test_pdf_object_serialize():
    class Point(PDFObject):
        def __init__(self, X=0, Y=0, **kwargs):
            super().__init__(**kwargs)
            self.X = X
            self.Y = Y

    class Square(PDFObject):
        def __init__(self, TopLeft, BottomRight, **kwargs):
            super().__init__(**kwargs)
            self.TopLeft = TopLeft
            self.BottomRight = BottomRight

    point_a = Point(id=1)
    point_b = Point(X=10, Y=10, id=2)
    square = Square(TopLeft=point_a, BottomRight=point_b, id=3)
    pdf_content = (
        point_a.serialize() + "\n" + point_b.serialize() + "\n" + square.serialize()
    )
    assert (
        pdf_content
        == """\
1 0 obj
<<
/X 0
/Y 0
>>
endobj
2 0 obj
<<
/X 10
/Y 10
>>
endobj
3 0 obj
<<
/TopLeft 1 0 R
/BottomRight 2 0 R
>>
endobj"""
    )


def test_empty_structure_tree():
    struct_builder = StructureTreeBuilder()
    assert (
        struct_builder.serialize()
        == """\
1 0 obj
<<
/Type /StructTreeRoot
/ParentTree 3 0 R
/K [2 0 R]
>>
endobj
2 0 obj
<<
/Type /StructElem
/S /Document
/P 1 0 R
/K []
>>
endobj
3 0 obj
<<
/Nums []
>>
endobj"""
    )


def test_single_image_structure_tree():
    images_alt_texts = (MarkedContent(1, 0, 0, "Image title", "Image description"),)
    struct_builder = StructureTreeBuilder(images_alt_texts)
    assert (
        struct_builder.serialize(first_object_id=3)
        == """\
3 0 obj
<<
/Type /StructTreeRoot
/ParentTree 5 0 R
/K [4 0 R]
>>
endobj
4 0 obj
<<
/Type /StructElem
/S /Document
/P 3 0 R
/K [6 0 R]
>>
endobj
5 0 obj
<<
/Nums [0 [6 0 R]]
>>
endobj
6 0 obj
<<
/Type /StructElem
/S /Figure
/P 4 0 R
/K [0]
/Pg 1 0 R
/T (Image title)
/Alt (Image description)
>>
endobj"""
    )
