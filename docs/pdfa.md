# PDF/A with fpdf2

## What is PDF/A

**PDF/A** is the ISO standard for long-term archiving of PDFs. It restricts features that aren’t stable for preservation (e.g., JavaScript, encryption, multimedia) and **requires self-containment** (fonts embedded, color spaces defined, predictable rendering).

---

## Choosing a PDF/A Profile

| Profile      | Description                                                                                                             | Actions Allowed                                                                                                                 | Actions Disallowed                                                                                                                                                                                              | Recommended Use Cases                                                                                             |
| ------------ | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **PDF/A-1B** | “B” = *Basic visual appearance*. Earliest profile, **based on PDF 1.4**; stricter feature set (no transparency/layers). | ✅ Embedding fonts<br>✅ JPEG/PNG/TIFF images (PDF 1.4 codecs)<br>✅ Digital signatures<br>✅ ICC OutputIntent for color management | ❌ Encryption<br>❌ JavaScript<br>❌ Multimedia (audio/video)<br>❌ External content dependencies<br>❌ Transparency (blend modes/soft masks)<br>❌ Layers (OCGs)<br>❌ JPEG2000 images<br>❌ Embedded file attachments | **Legacy/long-term archives** needing maximum compatibility; **scanned documents** where appearance is paramount. |
| **PDF/A-2B** | “B” = *Basic visual appearance*. Ensures documents can be reliably rendered visually. Based on PDF 1.7.                 | ✅ Embedding fonts<br>✅ JPEG/JPEG2000/PNG/TIFF images<br>✅ Transparency<br>✅ Layers (OCGs)<br>✅ Digital signatures               | ❌ Encryption<br>❌ JavaScript<br>❌ Multimedia (audio/video)<br>❌ External content dependencies                                                                                                                   | **Scanned documents** where only appearance must be preserved (invoices, contracts for viewing).                  |
| **PDF/A-2U** | Adds “U” = *Unicode text mapping*. Same as 2B + text must be Unicode-mapped for reliable search/extract.                | ✅ Same as 2B<br>✅ Text extractable & searchable                                                                                 | ❌ Same restrictions as 2B                                                                                                                                                                                       | **Searchable archives** (legal texts, regulations, scientific articles).                                          |
| **PDF/A-3B** | Like 2B, **plus** allows embedding *arbitrary files* as attachments (XML, CSV, DOCX, etc.).                             | ✅ Same as 2B<br>✅ Embed external files **inside** the PDF                                                                       | ❌ Encryption<br>❌ JavaScript<br>❌ Multimedia                                                                                                                                                                    | **Compound documents** (e-invoices with XML, submissions needing source data).                                    |
| **PDF/A-3U** | 3B + Unicode requirement for text.                                                                                      | ✅ Same as 3B + searchable text                                                                                                  | ❌ Same as 3B                                                                                                                                                                                                    | **Archival packages** that need attachments + searchable text.                                                    |
| **PDF/A-4**  | Based on PDF 2.0 (ISO 32000-2). Simplified model; no A/B/U tiers—modern baseline.                                       | ✅ Unicode text mapping<br>✅ Attachments allowed<br>✅ Transparency, layers, signatures                                           | ❌ Encryption<br>❌ JavaScript<br>❌ Multimedia                                                                                                                                                                    | **Modern general-purpose archiving** for libraries, government, enterprises.                                      |
| **PDF/A-4E** | “E” = *Engineering*. Tailored for engineering/CAD workflows; supports 3D model containers.                              | ✅ Same as 4<br>✅ Engineering/CAD payloads (e.g., model data)                                                                    | ❌ Encryption<br>❌ JavaScript<br>❌ Non-archival multimedia                                                                                                                                                       | **Engineering & CAD archiving** (technical drawings, 3D models, BOMs).                                            |
| **PDF/A-4F** | “F” = *File attachments*. Focused on embedded companion files.                                                          | ✅ Same as 4<br>✅ File attachments emphasized                                                                                    | ❌ Encryption<br>❌ JavaScript<br>❌ Multimedia                                                                                                                                                                    | **Data-centric bundles** (PDF + XML/CSV/JSON source files).                                                       |

---

## How to produce PDF/A with fpdf2

### Pick a profile at construction time

```python
from fpdf import FPDF
from fpdf.enums import DocumentCompliance

pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_4)
```

* When `enforce_compliance` is set, **fpdf2 actively prevents non-compliant operations** and will raise errors if you try something forbidden for the selected profile.

### Quick example

```python
pdf = FPDF(enforce_compliance=DocumentCompliance.PDFA_4)
pdf.add_page()
pdf.set_font("Helvetica", size=12)
pdf.cell(0, 10, "Modern archival PDF, PDF 2.0 based.")
pdf.output("example-4.pdf")
```

---

## Future: Accessible documents (WCAG/PDF/UA)

To enable PDF/A 2A and 3A compliance FPDF needs to be able to produce accessible documents.
Those features need to be implemented:

* **Tagged PDFs** (logical structure, reading order)
* **Alt text** for images, meaningful link text
* **Color contrast** and keyboard-navigable annotations
