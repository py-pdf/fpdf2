from fpdf.outline import InternalLink, OutlineSection, serialize_outline


def test_serialize_outline():
    sections = (
        OutlineSection(
            "Title 1", level=0, page_number=1, internal_link=InternalLink(1, 0)
        ),
        OutlineSection(
            "Subtitle 1.1", level=1, page_number=1, internal_link=InternalLink(2, 0)
        ),
        OutlineSection(
            "Title 2", level=0, page_number=1, internal_link=InternalLink(3, 0)
        ),
        OutlineSection(
            "Subtitle 2.1", level=1, page_number=1, internal_link=InternalLink(4, 0)
        ),
        OutlineSection(
            "Subtitle 2.2", level=1, page_number=1, internal_link=InternalLink(5, 0)
        ),
    )
    assert (
        serialize_outline(sections, first_object_id=6)
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
/Dest [1 0 R /XYZ 0 0.00 null]
/First 8 0 R
/Last 8 0 R
/Next 9 0 R
/Parent 6 0 R
/Title (Title 1)
>>
endobj
8 0 obj
<<
/Count 0
/Dest [2 0 R /XYZ 0 0.00 null]
/Parent 7 0 R
/Title (Subtitle 1.1)
>>
endobj
9 0 obj
<<
/Count 2
/Dest [3 0 R /XYZ 0 0.00 null]
/First 10 0 R
/Last 11 0 R
/Parent 6 0 R
/Prev 7 0 R
/Title (Title 2)
>>
endobj
10 0 obj
<<
/Count 0
/Dest [4 0 R /XYZ 0 0.00 null]
/Next 11 0 R
/Parent 9 0 R
/Title (Subtitle 2.1)
>>
endobj
11 0 obj
<<
/Count 0
/Dest [5 0 R /XYZ 0 0.00 null]
/Parent 9 0 R
/Prev 10 0 R
/Title (Subtitle 2.2)
>>
endobj"""
    )
