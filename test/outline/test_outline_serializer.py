from fpdf.outline import OutlineSection, serialize_outline
from fpdf.syntax import DestinationXYZ


def test_serialize_outline():
    sections = (
        OutlineSection("Title 1", level=0, page_number=1, dest=DestinationXYZ(page=1)),
        OutlineSection(
            "Subtitle 1.1", level=1, page_number=1, dest=DestinationXYZ(page=2)
        ),
        OutlineSection("Title 2", level=0, page_number=1, dest=DestinationXYZ(page=3)),
        OutlineSection(
            "Subtitle 2.1", level=1, page_number=1, dest=DestinationXYZ(page=4)
        ),
        OutlineSection(
            "Subtitle 2.2", level=1, page_number=1, dest=DestinationXYZ(page=5)
        ),
    )
    assert (
        serialize_outline(sections, first_object_id=6)
        == f"""\
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
/Title ({'Title 1'.encode('UTF-16').decode('latin-1')})
>>
endobj
8 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 7 0 R
/Title ({'Subtitle 1.1'.encode('UTF-16').decode('latin-1')})
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
/Title ({'Title 2'.encode('UTF-16').decode('latin-1')})
>>
endobj
10 0 obj
<<
/Count 0
/Dest [9 0 R /XYZ 0 0 null]
/Next 11 0 R
/Parent 9 0 R
/Title ({'Subtitle 2.1'.encode('UTF-16').decode('latin-1')})
>>
endobj
11 0 obj
<<
/Count 0
/Dest [11 0 R /XYZ 0 0 null]
/Parent 9 0 R
/Prev 10 0 R
/Title ({'Subtitle 2.2'.encode('UTF-16').decode('latin-1')})
>>
endobj"""
    )


def test_serialize_outline_with_headless_hierarchy():  # issues 239
    sections = (
        OutlineSection("?-1", level=1, page_number=2, dest=DestinationXYZ(page=2)),
        OutlineSection("?-1-1", level=2, page_number=2, dest=DestinationXYZ(page=2)),
        OutlineSection("1", level=0, page_number=2, dest=DestinationXYZ(page=2)),
        OutlineSection("1-1", level=1, page_number=2, dest=DestinationXYZ(page=2)),
        OutlineSection("1-1-1", level=2, page_number=2, dest=DestinationXYZ(page=2)),
    )
    assert (
        serialize_outline(sections, first_object_id=6)
        == f"""\
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
/Title ({'?-1'.encode('UTF-16').decode('latin-1')})
>>
endobj
8 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 7 0 R
/Title ({'?-1-1'.encode('UTF-16').decode('latin-1')})
>>
endobj
9 0 obj
<<
/Count 1
/Dest [5 0 R /XYZ 0 0 null]
/First 10 0 R
/Last 10 0 R
/Parent 6 0 R
/Title ({'1'.encode('UTF-16').decode('latin-1')})
>>
endobj
10 0 obj
<<
/Count 1
/Dest [5 0 R /XYZ 0 0 null]
/First 11 0 R
/Last 11 0 R
/Parent 9 0 R
/Title ({'1-1'.encode('UTF-16').decode('latin-1')})
>>
endobj
11 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0 null]
/Parent 10 0 R
/Title ({'1-1-1'.encode('UTF-16').decode('latin-1')})
>>
endobj"""
    )
