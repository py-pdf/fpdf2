from typing import NamedTuple

from fpdf.outline import OutlineSection, build_outline_objs
from fpdf.syntax import DestinationXYZ, PDFString


class DummyWithId(NamedTuple):
    id: int


def _serialize_outline(sections, first_object_id=1):
    n = first_object_id
    page_objs = {i: DummyWithId(2 * i + 3) for i in range(len(sections))}
    outline_objs = list(build_outline_objs(sections, page_objs))
    for obj in outline_objs:
        obj.id = n
        n += 1
    output = "\n".join(obj.serialize() for obj in outline_objs)
    return output


def test_serialize_outline():
    sections = (
        OutlineSection(
            "Title 1", level=0, page_number=1, dest=DestinationXYZ(page=1, top=0)
        ),
        OutlineSection(
            "Subtitle 1.1", level=1, page_number=1, dest=DestinationXYZ(page=2, top=0)
        ),
        OutlineSection(
            "Title 2", level=0, page_number=1, dest=DestinationXYZ(page=3, top=0)
        ),
        OutlineSection(
            "Subtitle 2.1", level=1, page_number=1, dest=DestinationXYZ(page=4, top=0)
        ),
        OutlineSection(
            "Subtitle 2.2", level=1, page_number=1, dest=DestinationXYZ(page=5, top=0)
        ),
    )
    assert (
        _serialize_outline(sections, first_object_id=6)
        == """\
6 0 obj
<<
/Count 2
/First 7 0 R
/Last 9 0 R
/Type /Outlines
>>
endobj
7 0 obj
<<
/Count 1
/Dest [3 0 R /XYZ 0 0 null]
/First 8 0 R
/Last 8 0 R
/Next 9 0 R
/Parent 6 0 R
/Title <feff005400690074006c006500200031>
>>
endobj
8 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 7 0 R
/Title <feff005300750062007400690074006c006500200031002e0031>
>>
endobj
9 0 obj
<<
/Count 2
/Dest [7 0 R /XYZ 0 0 null]
/First 10 0 R
/Last 11 0 R
/Parent 6 0 R
/Prev 7 0 R
/Title <feff005400690074006c006500200032>
>>
endobj
10 0 obj
<<
/Count 0
/Dest [9 0 R /XYZ 0 0 null]
/Next 11 0 R
/Parent 9 0 R
/Title <feff005300750062007400690074006c006500200032002e0031>
>>
endobj
11 0 obj
<<
/Count 0
/Dest [11 0 R /XYZ 0 0 null]
/Parent 9 0 R
/Prev 10 0 R
/Title <feff005300750062007400690074006c006500200032002e0032>
>>
endobj"""
    )


def test__serialize_outline_with_headless_hierarchy():  # issues 239
    sections = (
        OutlineSection(
            "?-1", level=1, page_number=2, dest=DestinationXYZ(page=2, top=0)
        ),
        OutlineSection(
            "?-1-1", level=2, page_number=2, dest=DestinationXYZ(page=2, top=0)
        ),
        OutlineSection("1", level=0, page_number=2, dest=DestinationXYZ(page=2, top=0)),
        OutlineSection(
            "1-1", level=1, page_number=2, dest=DestinationXYZ(page=2, top=0)
        ),
        OutlineSection(
            "1-1-1", level=2, page_number=2, dest=DestinationXYZ(page=2, top=0)
        ),
    )
    assert (
        _serialize_outline(sections, first_object_id=6)
        == """\
6 0 obj
<<
/Count 2
/First 7 0 R
/Last 9 0 R
/Type /Outlines
>>
endobj
7 0 obj
<<
/Count 1
/Dest [5 0 R /XYZ 0 0 null]
/First 8 0 R
/Last 8 0 R
/Parent 6 0 R
/Title <feff003f002d0031>
>>
endobj
8 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 7 0 R
/Title <feff003f002d0031002d0031>
>>
endobj
9 0 obj
<<
/Count 1
/Dest [5 0 R /XYZ 0 0 null]
/First 10 0 R
/Last 10 0 R
/Parent 6 0 R
/Title <feff0031>
>>
endobj
10 0 obj
<<
/Count 1
/Dest [5 0 R /XYZ 0 0 null]
/First 11 0 R
/Last 11 0 R
/Parent 9 0 R
/Title <feff0031002d0031>
>>
endobj
11 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 10 0 R
/Title <feff0031002d0031002d0031>
>>
endobj"""
    )


def test__serialize_outline_without_hex_encoding():  # issue-458
    PDFString.USE_HEX_ENCODING = False
    try:
        sections = (
            OutlineSection(
                "Title", level=0, page_number=1, dest=DestinationXYZ(page=1, top=0)
            ),
        )
        assert (
            _serialize_outline(sections, first_object_id=1)
            == f"""\
1 0 obj
<<
/Count 1
/First 2 0 R
/Last 2 0 R
/Type /Outlines
>>
endobj
2 0 obj
<<
/Count 0
/Dest [3 0 R /XYZ 0 0 null]
/Parent 1 0 R
/Title ({'Title'.encode('UTF-16').decode('latin-1')})
>>
endobj"""
        )
    finally:
        PDFString.USE_HEX_ENCODING = True  # restore default value
