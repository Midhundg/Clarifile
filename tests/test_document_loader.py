"""Unit tests for DocumentLoader across all supported formats (PDF, DOCX, TXT, CSV, XLSX)."""

import io
import pytest
import docx
import pandas as pd
from services.document_loader import DocumentLoader, DocumentExtractionError, EmptyDocumentError


def create_minimal_pdf_bytes(text: str = "Clarifile Automated PDF Test Content") -> bytes:
    """Create minimal valid PDF byte string with extractable text."""
    stream_content = f"BT\n/F1 12 Tf\n72 712 Td\n({text}) Tj\nET\n".encode("latin-1")
    length = len(stream_content)

    return f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {length} >> stream
""".encode("latin-1") + stream_content + b"""endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000249 00000 n 
0000000352 00000 n 
trailer << /Root 1 0 R /Size 6 >>
startxref
426
%%EOF"""


def test_pdf_extraction():
    """Test extracting text and page metadata from a PDF file."""
    pdf_bytes = create_minimal_pdf_bytes("Clarifile Automated PDF Test Content")
    doc = DocumentLoader.load_document(pdf_bytes, "sample.pdf")

    assert doc.file_name == "sample.pdf"
    assert doc.file_type == "pdf"
    assert doc.num_pages >= 1
    assert "Clarifile Automated PDF Test Content" in doc.full_text
    assert doc.pages[0].page_number == 1


def test_docx_extraction():
    """Test extracting paragraphs and structured tables from DOCX."""
    doc_obj = docx.Document()
    doc_obj.add_paragraph("First paragraph of docx specification.")
    doc_obj.add_paragraph("Second paragraph detailing architectural components.")

    table = doc_obj.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Accuracy"
    table.cell(1, 1).text = "99.5%"

    buf = io.BytesIO()
    doc_obj.save(buf)
    docx_bytes = buf.getvalue()

    doc = DocumentLoader.load_document(docx_bytes, "report.docx")

    assert doc.file_type == "docx"
    assert "First paragraph of docx specification." in doc.full_text
    assert "Accuracy | 99.5%" in doc.full_text
    assert doc.num_pages == 1


def test_txt_extraction():
    """Test extracting plain text files."""
    text_content = "Clarifile plain text test document.\nLine 2 with crucial system facts."
    txt_bytes = text_content.encode("utf-8")

    doc = DocumentLoader.load_document(txt_bytes, "notes.txt")

    assert doc.file_type == "txt"
    assert "Clarifile plain text test document." in doc.full_text
    assert doc.total_words > 0


def test_txt_latin1_fallback():
    """Test extracting plain text with non-UTF-8 encoding."""
    text_content = "Special character: café and résumé in Latin-1"
    latin_bytes = text_content.encode("latin-1")

    doc = DocumentLoader.load_document(latin_bytes, "french_notes.txt")
    assert "café" in doc.full_text or "caf" in doc.full_text


def test_csv_extraction():
    """Test extracting tabular CSV content with headers and preview."""
    csv_text = "Department,Budget,Headcount\nEngineering,500000,25\nResearch,350000,12\n"
    csv_bytes = csv_text.encode("utf-8")

    doc = DocumentLoader.load_document(csv_bytes, "departments.csv")

    assert doc.file_type == "csv"
    assert "Engineering" in doc.full_text
    assert "Budget" in doc.full_text
    assert "Headcount" in doc.full_text


def test_excel_extraction():
    """Test extracting multi-sheet Excel workbooks with sheet metadata."""
    df1 = pd.DataFrame({"Project": ["Clarifile", "VectorDB"], "Status": ["Active", "Deployed"]})
    df2 = pd.DataFrame({"Quarter": ["Q1", "Q2"], "Revenue": [100000, 150000]})

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Projects", index=False)
        df2.to_excel(writer, sheet_name="Financials", index=False)

    excel_bytes = buf.getvalue()
    doc = DocumentLoader.load_document(excel_bytes, "company_data.xlsx")

    assert doc.file_type == "xlsx"
    assert doc.num_pages == 2
    sheet_names = [p.page_number for p in doc.pages]
    assert "Projects" in sheet_names
    assert "Financials" in sheet_names
    assert "Clarifile" in doc.full_text
    assert "Revenue" in doc.full_text


def test_empty_document_handling():
    """Test that empty documents raise EmptyDocumentError."""
    with pytest.raises(EmptyDocumentError):
        DocumentLoader.load_document(b"   \n\t  ", "empty.txt")


def test_pages_extraction():
    """Test extracting text from an Apple Pages archive containing QuickLook preview."""
    import zipfile
    pdf_bytes = create_minimal_pdf_bytes("Clarifile Apple Pages Content")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("QuickLook/Preview.pdf", pdf_bytes)

    pages_bytes = buf.getvalue()
    doc = DocumentLoader.load_document(pages_bytes, "project_notes.pages")

    assert doc.file_type == "pages"
    assert "Clarifile Apple Pages Content" in doc.full_text
    assert doc.num_pages >= 1


def test_pages_extraction_nested_index_zip():
    """Test extracting text from modern Apple Pages with nested Index.zip and snappy iwa."""
    import zipfile

    content = b"Database Management Systems (DBMS) lecture notes: Relational Model, SQL, Transactions, ACID Properties."
    L = len(content)
    snappy_block = bytes([L, 240, L - 1]) + content
    header = bytes([0x00, len(snappy_block) & 0xFF, (len(snappy_block) >> 8) & 0xFF, 0x00])
    iwa_data = header + snappy_block

    # Nested Index.zip
    inner_buf = io.BytesIO()
    with zipfile.ZipFile(inner_buf, "w") as iz:
        iz.writestr("Document.iwa", iwa_data)
    inner_bytes = inner_buf.getvalue()

    # Outer .pages zip
    outer_buf = io.BytesIO()
    with zipfile.ZipFile(outer_buf, "w") as oz:
        oz.writestr("Index.zip", inner_bytes)
    pages_bytes = outer_buf.getvalue()

    doc = DocumentLoader.load_document(pages_bytes, "DBMS.pages")
    assert doc.file_type == "pages"
    assert "Database Management Systems" in doc.full_text
    assert "ACID Properties" in doc.full_text


def test_pages_extraction_uncompressed_folder_error():
    """Test that a non-zip Apple Pages folder bundle raises an informative error."""
    with pytest.raises(DocumentExtractionError) as exc_info:
        DocumentLoader.load_document(b"not a zip file content", "mac_notes.pages")
    assert "Export To > PDF" in str(exc_info.value)


def test_unsupported_format_handling():
    """Test that unsupported formats raise DocumentExtractionError."""
    with pytest.raises(DocumentExtractionError):
        DocumentLoader.load_document(b"random binary data", "archive.zip")
