"""Document Extraction Engine for Clarifile.

Supports PDF, DOCX, TXT, CSV, and XLSX formats with detailed page/worksheet metadata.
"""

import io
import zipfile
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union
import PyPDF2
import docx
import pandas as pd

from utils.validators import sanitize_filename, validate_file_upload
from utils.helpers import generate_doc_id


class DocumentExtractionError(Exception):
    """Exception raised when document extraction fails."""
    pass


class EmptyDocumentError(DocumentExtractionError):
    """Exception raised when an extracted document contains no readable text."""
    pass


@dataclass
class DocumentPage:
    """Represents a single page, sheet, or section within an extracted document."""
    page_number: Union[int, str]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    """Represents an extracted document with metadata and separated pages."""
    doc_id: str
    file_name: str
    file_type: str
    file_size: int
    pages: List[DocumentPage]
    full_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_pages(self) -> int:
        return len(self.pages)

    @property
    def total_words(self) -> int:
        return len(self.full_text.split())

    @property
    def total_chars(self) -> int:
        return len(self.full_text)


class DocumentLoader:
    """Service to load and extract text and metadata from supported file formats."""

    @classmethod
    def load_document(
        cls,
        file_source: Union[bytes, io.BytesIO, Any],
        file_name: str,
        file_size: int = 0
    ) -> ExtractedDocument:
        """Load and extract text from a file source.

        Args:
            file_source: File bytes, BytesIO, or Streamlit UploadedFile object.
            file_name: Name of the file.
            file_size: Size in bytes (optional, computed if not provided).

        Returns:
            ExtractedDocument containing pages and metadata.

        Raises:
            DocumentExtractionError: If extraction fails or file is unsupported/corrupted.
            EmptyDocumentError: If file has no readable text.
        """
        clean_name = sanitize_filename(file_name)

        # Get bytes from source
        if hasattr(file_source, "read"):
            content_bytes = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
        elif isinstance(file_source, bytes):
            content_bytes = file_source
        else:
            raise DocumentExtractionError(f"Unsupported file source type: {type(file_source)}")

        computed_size = file_size if file_size > 0 else len(content_bytes)

        # Validate file
        is_valid, error_msg = validate_file_upload(clean_name, computed_size)
        if not is_valid:
            raise DocumentExtractionError(error_msg)

        ext = clean_name.rsplit(".", 1)[1].lower()
        doc_id = generate_doc_id(clean_name, content_bytes)

        try:
            if ext == "pdf":
                pages = cls._extract_pdf(content_bytes, clean_name)
            elif ext == "docx":
                pages = cls._extract_docx(content_bytes, clean_name)
            elif ext == "txt":
                pages = cls._extract_txt(content_bytes, clean_name)
            elif ext == "csv":
                pages = cls._extract_csv(content_bytes, clean_name)
            elif ext == "xlsx":
                pages = cls._extract_excel(content_bytes, clean_name)
            elif ext == "pages":
                pages = cls._extract_pages(content_bytes, clean_name)
            else:
                raise DocumentExtractionError(f"Unsupported document format: .{ext}")
        except EmptyDocumentError:
            raise
        except Exception as e:
            raise DocumentExtractionError(f"Failed to extract content from '{clean_name}': {str(e)}") from e

        # Assemble full text
        page_texts = [p.text for p in pages if p.text and p.text.strip()]
        full_text = "\n\n".join(page_texts).strip()

        if not full_text:
            raise EmptyDocumentError(
                f"The document '{clean_name}' contains no readable or extractable text content."
            )

        metadata = {
            "file_name": clean_name,
            "file_type": ext,
            "file_size": computed_size,
            "page_count": len(pages),
            "doc_id": doc_id,
        }

        return ExtractedDocument(
            doc_id=doc_id,
            file_name=clean_name,
            file_type=ext,
            file_size=computed_size,
            pages=pages,
            full_text=full_text,
            metadata=metadata
        )

    @staticmethod
    def _extract_pdf(content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract text page by page from PDF bytes."""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
        except Exception as e:
            raise DocumentExtractionError(f"Corrupted or invalid PDF file: {str(e)}")

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise DocumentExtractionError("PDF is password protected and cannot be read.")

        pages: List[DocumentPage] = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            pages.append(
                DocumentPage(
                    page_number=i,
                    text=page_text.strip(),
                    metadata={"page_number": i, "file_name": file_name}
                )
            )

        has_text = any(p.text.strip() for p in pages)
        if not has_text:
            raise EmptyDocumentError(f"PDF '{file_name}' contains no extractable text (may be image-only/scanned).")

        return pages

    @staticmethod
    def _extract_docx(content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract paragraphs and tables from DOCX bytes."""
        try:
            doc = docx.Document(io.BytesIO(content_bytes))
        except Exception as e:
            raise DocumentExtractionError(f"Corrupted or invalid DOCX file: {str(e)}")

        sections_text: List[str] = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                sections_text.append(text)

        # Extract tables
        for table_idx, table in enumerate(doc.tables, start=1):
            table_lines: List[str] = []
            for row in table.rows:
                row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                if any(row_cells):
                    table_lines.append(" | ".join(row_cells))
            if table_lines:
                table_text = f"[Table {table_idx}]\n" + "\n".join(table_lines)
                sections_text.append(table_text)

        if not sections_text:
            raise EmptyDocumentError(f"DOCX '{file_name}' contains no readable paragraphs or tables.")

        combined_text = "\n\n".join(sections_text)
        return [
            DocumentPage(
                page_number=1,
                text=combined_text,
                metadata={"page_number": 1, "file_name": file_name, "section_count": len(sections_text)}
            )
        ]

    @staticmethod
    def _extract_txt(content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract text from plain text file using multiple encodings."""
        text = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise DocumentExtractionError(f"Could not decode text file '{file_name}' using standard encodings.")

        cleaned = text.strip()
        if not cleaned:
            raise EmptyDocumentError(f"Text file '{file_name}' is empty.")

        return [
            DocumentPage(
                page_number=1,
                text=cleaned,
                metadata={"page_number": 1, "file_name": file_name}
            )
        ]

    @staticmethod
    def _extract_csv(content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract structured tabular text from CSV."""
        try:
            df = pd.read_csv(io.BytesIO(content_bytes))
        except Exception as e:
            raise DocumentExtractionError(f"Failed to parse CSV '{file_name}': {str(e)}")

        if df.empty:
            raise EmptyDocumentError(f"CSV file '{file_name}' has no rows.")

        lines = [
            f"CSV Document: {file_name}",
            f"Columns ({len(df.columns)}): {', '.join([str(c) for c in df.columns])}",
            f"Total Rows: {len(df)}",
            "",
            "Data Preview:",
            df.to_string(index=False, max_rows=100)
        ]
        text_content = "\n".join(lines)

        return [
            DocumentPage(
                page_number=1,
                text=text_content,
                metadata={"page_number": 1, "file_name": file_name, "row_count": len(df), "col_count": len(df.columns)}
            )
        ]

    @staticmethod
    def _extract_excel(content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract each worksheet from Excel file as a separate page."""
        try:
            excel_file = pd.ExcelFile(io.BytesIO(content_bytes), engine="openpyxl")
        except Exception as e:
            raise DocumentExtractionError(f"Failed to open Excel workbook '{file_name}': {str(e)}")

        pages: List[DocumentPage] = []
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if df.empty:
                    continue
                sheet_lines = [
                    f"Worksheet: {sheet_name}",
                    f"Columns ({len(df.columns)}): {', '.join([str(c) for c in df.columns])}",
                    f"Total Rows: {len(df)}",
                    "",
                    df.to_string(index=False, max_rows=100)
                ]
                pages.append(
                    DocumentPage(
                        page_number=sheet_name,
                        text="\n".join(sheet_lines),
                        metadata={"sheet_name": sheet_name, "file_name": file_name, "rows": len(df)}
                    )
                )
            except Exception:
                continue

        if not pages:
            raise EmptyDocumentError(f"Excel workbook '{file_name}' contains no readable data in any sheet.")

        return pages

    @classmethod
    def _extract_pages(cls, content_bytes: bytes, file_name: str) -> List[DocumentPage]:
        """Extract text from Apple Pages (.pages) documents.

        Supports:
        1. Embedded QuickLook/Preview.pdf (maximum layout and page fidelity).
        2. Legacy index.xml (pre-2013 iWork formats).
        3. Modern Index/*.iwa Snappy decompression and string parsing from root or Index.zip.
        4. Raw string stream scanning fallback for robustness.
        """
        try:
            zip_buffer = io.BytesIO(content_bytes)
            if not zipfile.is_zipfile(zip_buffer):
                raise DocumentExtractionError(
                    f"'{file_name}' appears to be saved as an uncompressed macOS folder package rather than a single archive.\n\n"
                    f"💡 Quick Fix: In Apple Pages on your Mac, choose: File > Export To > PDF (or Word), then upload the exported file."
                )

            with zipfile.ZipFile(zip_buffer) as z:
                namelist = z.namelist()

                # 1. Check for QuickLook preview PDF (standard in Apple Pages when saved with preview)
                for preview_path in [
                    "QuickLook/Preview.pdf", "preview.pdf", "QuickLook/preview.pdf",
                    "Preview.pdf", "QuickLook/Preview.PDF"
                ]:
                    if preview_path in namelist:
                        pdf_data = z.read(preview_path)
                        pages = cls._extract_pdf(pdf_data, file_name)
                        for p in pages:
                            p.metadata["file_name"] = file_name
                            p.metadata["source_format"] = "pages_quicklook"
                        return pages

                # 2. Check for legacy index.xml
                for xml_name in ["index.xml", "Index.xml"]:
                    if xml_name in namelist:
                        import xml.etree.ElementTree as ET
                        xml_content = z.read(xml_name)
                        root = ET.fromstring(xml_content)
                        texts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
                        if texts:
                            combined = "\n\n".join(texts)
                            return [
                                DocumentPage(
                                    page_number=1,
                                    text=combined,
                                    metadata={"page_number": 1, "file_name": file_name, "source_format": "pages_xml"}
                                )
                            ]

                # 3. Gather all .iwa files (both root archive and nested Index.zip)
                iwa_entries: List[Tuple[str, bytes]] = []

                # Direct .iwa in root zip
                for name in namelist:
                    if name.lower().endswith(".iwa"):
                        try:
                            iwa_entries.append((name, z.read(name)))
                        except Exception:
                            pass

                # Check for nested Index.zip (common in modern iWork Pages files)
                for name in namelist:
                    if name.lower().endswith(".zip"):
                        try:
                            inner_bytes = z.read(name)
                            if zipfile.is_zipfile(io.BytesIO(inner_bytes)):
                                with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner_z:
                                    for inner_name in inner_z.namelist():
                                        if inner_name.lower().endswith(".iwa"):
                                            try:
                                                iwa_entries.append((inner_name, inner_z.read(inner_name)))
                                            except Exception:
                                                pass
                        except Exception:
                            pass

                if iwa_entries:
                    all_snippets: List[str] = []
                    # Prioritize Document.iwa
                    iwa_entries.sort(key=lambda x: 0 if "document" in x[0].lower() else 1)

                    for iwa_name, raw_data in iwa_entries:
                        decompressed = cls._decompress_iwa(raw_data)
                        extracted_text = cls._extract_strings_from_bytes(decompressed)
                        if extracted_text and len(extracted_text) >= 15:
                            all_snippets.append(extracted_text)
                        else:
                            # Fallback: string scanning directly from raw bytes if decompression was empty
                            raw_strings = cls._extract_strings_from_bytes(raw_data)
                            if raw_strings and len(raw_strings) >= 15:
                                all_snippets.append(raw_strings)

                    if all_snippets:
                        combined_text = "\n\n".join(all_snippets)
                        return [
                            DocumentPage(
                                page_number=1,
                                text=combined_text.strip(),
                                metadata={"page_number": 1, "file_name": file_name, "source_format": "pages_iwa"}
                            )
                        ]

        except EmptyDocumentError:
            raise
        except DocumentExtractionError:
            raise
        except Exception as e:
            raise DocumentExtractionError(f"Failed to process Pages file '{file_name}': {str(e)}") from e

        raise DocumentExtractionError(
            f"Apple Pages file '{file_name}' contains no readable preview or text streams.\n\n"
            f"💡 Quick Fix: In Apple Pages on your Mac, click File > Export To > PDF (or Word .docx), then upload the exported PDF."
        )

    @classmethod
    def _decompress_iwa(cls, data: bytes) -> bytes:
        """Decompress framed Snappy chunks inside an Apple .iwa file."""
        out = bytearray()
        pos = 0
        while pos + 4 <= len(data):
            # Apple iWork IWA framing:
            # Byte 0: Chunk Type (0x00 = Snappy-compressed block)
            # Bytes 1-3: 24-bit unsigned integer (little-endian) representing payload length
            chunk_type = data[pos]
            frame_len = data[pos+1] | (data[pos+2] << 8) | (data[pos+3] << 16)
            pos += 4
            if frame_len <= 0 or pos + frame_len > len(data):
                out.extend(data[pos:])
                break
            frame_data = data[pos : pos + frame_len]
            pos += frame_len
            try:
                if chunk_type == 0:
                    chunk = cls._decompress_snappy_chunk(frame_data)
                    out.extend(chunk)
                else:
                    out.extend(frame_data)
            except Exception:
                out.extend(frame_data)
        return bytes(out) if out else data

    @staticmethod
    def _decompress_snappy_chunk(data: bytes) -> bytes:
        """Decompress a single raw Snappy block in pure Python."""
        pos = 0
        uncompressed_len = 0
        shift = 0
        while pos < len(data):
            b = data[pos]
            pos += 1
            uncompressed_len |= (b & 0x7f) << shift
            if not (b & 0x80):
                break
            shift += 7

        out = bytearray()
        while pos < len(data):
            tag_byte = data[pos]
            pos += 1
            tag = tag_byte & 0x03
            if tag == 0:  # Literal
                length = (tag_byte >> 2) + 1
                if length > 60:
                    extra = length - 60
                    length = int.from_bytes(data[pos : pos + extra], "little") + 1
                    pos += extra
                out.extend(data[pos : pos + length])
                pos += length
            elif tag == 1:  # 1-byte copy
                length = ((tag_byte >> 2) & 0x07) + 4
                offset = ((tag_byte & 0xe0) << 3) | data[pos]
                pos += 1
                for _ in range(length):
                    out.append(out[-offset])
            elif tag == 2:  # 2-byte copy
                length = (tag_byte >> 2) + 1
                offset = int.from_bytes(data[pos : pos + 2], "little")
                pos += 2
                for _ in range(length):
                    out.append(out[-offset])
            elif tag == 3:  # 4-byte copy
                length = (tag_byte >> 2) + 1
                offset = int.from_bytes(data[pos : pos + 4], "little")
                pos += 4
                for _ in range(length):
                    out.append(out[-offset])
        return bytes(out)

    @staticmethod
    def _extract_strings_from_bytes(raw_bytes: bytes) -> str:
        """Extract printable content strings from decompressed protobuf bytes."""
        import re
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = raw_bytes.decode("latin-1", errors="ignore")

        tokens = re.findall(r"[\w\s\.,;:!?\(\)\[\]\{\}\-\+\*\/=<>@#\$%&'\"]{3,}", text, re.UNICODE)
        ignored_prefixes = (
            "TSWP.", "KN.", "TST.", "TSD.", "TSP.", "TSK.", "UUID",
            "com.apple.", "org.oasis", "http://", "https://", "schemas.openxml"
        )
        clean = []
        seen = set()
        for t in tokens:
            t_clean = t.strip()
            if (
                len(t_clean) >= 2
                and any(c.isalnum() for c in t_clean)
                and not any(t_clean.startswith(p) for p in ignored_prefixes)
                and len(t_clean) < 2000
            ):
                alpha_count = sum(1 for c in t_clean if c.isalnum() or c.isspace())
                if alpha_count / len(t_clean) > 0.5:
                    if t_clean not in seen:
                        seen.add(t_clean)
                        clean.append(t_clean)
        return "\n".join(clean)
