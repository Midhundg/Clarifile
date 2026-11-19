"""Script to generate professional PDF and DOCX documentation for Clarifile."""

import os
from datetime import datetime

# ReportLab imports for PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

# python-docx imports for Word
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def build_pdf(filename: str):
    """Generate a clean, high-standard PDF document."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0066CC"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "DocBullet",
        parent=body_style,
        leftIndent=15,
        spaceAfter=3,
    )
    code_style = ParagraphStyle(
        "DocCode",
        parent=body_style,
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=4,
        spaceAfter=6,
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )
    td_style = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Title & Header
    story.append(Paragraph("Clarifile — Intelligent File Analyzer", title_style))
    story.append(Paragraph("Comprehensive Technical Architecture, Tech Stack, & System Workflows", subtitle_style))
    story.append(Paragraph("<b>Version:</b> 1.0 Production &nbsp;|&nbsp; <b>Framework:</b> Modular RAG & Document Intelligence &nbsp;|&nbsp; <b>Date:</b> November 2026", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0066CC"), spaceBefore=8, spaceAfter=14))

    # Section 1: Executive Overview
    story.append(Paragraph("1. Executive Overview & Mission", h1_style))
    story.append(Paragraph(
        "<b>Clarifile</b> is a production-grade, modular Document Intelligence and Retrieval-Augmented Generation (RAG) platform. "
        "It solves the problem of information silos by ingesting unstructured multi-format files, converting them into mathematically "
        "indexed vector spaces, and allowing authenticated users to converse with their files, extract multi-tier executive summaries, "
        "and perform comparative side-by-side technical analyses. Each user account operates in a completely isolated sandbox with "
        "dedicated vector collections, preventing data leakage across users.",
        body_style,
    ))

    # Section 2: Tools & Technologies Stack Table
    story.append(Paragraph("2. Tools & Technology Stack", h1_style))
    tech_data = [
        [Paragraph("Category", th_style), Paragraph("Technology / Library", th_style), Paragraph("Specification", th_style), Paragraph("Role in System", th_style)],
        [Paragraph("Frontend UI", td_style), Paragraph("Streamlit", td_style), Paragraph("1.35+", td_style), Paragraph("Reactive web interface, reactive session routing, BaseWeb UI styling.", td_style)],
        [Paragraph("Dense Vectors", td_style), Paragraph("SentenceTransformers", td_style), Paragraph("all-MiniLM-L6-v2", td_style), Paragraph("384-dimensional dense semantic embeddings with L2 normalization.", td_style)],
        [Paragraph("Vector Database", td_style), Paragraph("ChromaDB", td_style), Paragraph("Persistent HNSW", td_style), Paragraph("Cosine similarity vector store with isolated per-user collections.", td_style)],
        [Paragraph("Keyword Search", td_style), Paragraph("Rank-BM25", td_style), Paragraph("Okapi BM25", td_style), Paragraph("Exact lexical keyword matching for technical codes, names, and metrics.", td_style)],
        [Paragraph("Rank Fusion", td_style), Paragraph("RRF Algorithm", td_style), Paragraph("k=60 Fusion", td_style), Paragraph("Harmonizes dense semantic and lexical sparse rankings with intent boost.", td_style)],
        [Paragraph("Generative LLM", td_style), Paragraph("Google Gemini API", td_style), Paragraph("gemini-3.8-flash", td_style), Paragraph("Grounded contextual reasoning, verified citations, executive summaries.", td_style)],
        [Paragraph("Multi-Format Parsers", td_style), Paragraph("PyPDF2, docx, openpyxl, snappy", td_style), Paragraph("Custom parsers", td_style), Paragraph("Parses PDF, DOCX, XLSX, CSV, TXT, and Apple Pages (.pages) archives.", td_style)],
        [Paragraph("Authentication", td_style), Paragraph("SQLite3 + hashlib", td_style), Paragraph("PBKDF2-HMAC-SHA256", td_style), Paragraph("100,000 rounds, 32-byte salts, unique usernames, tenant isolation.", td_style)],
        [Paragraph("Test Suite", td_style), Paragraph("pytest", td_style), Paragraph("32 Tests (100%)", td_style), Paragraph("Automated unit and integration testing across all RAG and auth flows.", td_style)],
    ]
    t = Table(tech_data, colWidths=[80, 110, 100, 240])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 3: Document Ingestion Pipeline Flow
    story.append(Paragraph("3. Document Ingestion Pipeline Flow", h1_style))
    story.append(Paragraph(
        "When a document is uploaded, it transitions through a strictly validated 4-stage pipeline:",
        body_style,
    ))
    story.append(Paragraph("• <b>Extraction (DocumentLoader):</b> Inspects file binary signatures. For Apple Pages, extracts embedded QuickLook PDFs or decompresses raw Snappy Protobuf .iwa frames. For PDFs, extracts page text. For DOCX, iterates paragraphs and table cells. For Excel/CSV, extracts cell values with sheet metadata.", bullet_style))
    story.append(Paragraph("• <b>Sentence-Aware Chunking (ChunkingService):</b> Splits extracted text into semantic passages of 800 characters with 150 characters overlap. Boundaries prioritize punctuation (periods, newlines) to prevent fragmented sentences. Every chunk retains document ID, filename, and page number.", bullet_style))
    story.append(Paragraph("• <b>Dense Vectorization (EmbeddingService):</b> Batch-vectorizes chunk text via all-MiniLM-L6-v2 into 384-dimensional floating-point vectors normalized to unit length.", bullet_style))
    story.append(Paragraph("• <b>Isolated Indexing (VectorStore):</b> Inserts embeddings and chunk metadata into the user's private ChromaDB collection (user_{username}_kb) in batches of 250 records.", bullet_style))

    # Section 4: Hybrid Retrieval & RAG Generation Flow
    story.append(Paragraph("4. Hybrid Retrieval & Grounded RAG Flow", h1_style))
    story.append(Paragraph(
        "Clarifile avoids the common failure modes of pure dense search (such as missing exact IDs or technical jargon) "
        "by utilizing a state-of-the-art Hybrid Search architecture:",
        body_style,
    ))
    story.append(Paragraph("• <b>Dense Retrieval:</b> Queries ChromaDB using HNSW cosine distance to find conceptually related chunks.", bullet_style))
    story.append(Paragraph("• <b>Sparse Okapi BM25:</b> Computes term-frequency inverse-document-frequency keyword relevance across all indexed chunks in the active scope.", bullet_style))
    story.append(Paragraph("• <b>Reciprocal Rank Fusion (RRF):</b> Aggregates both ranked candidate sets using RRF(d) = sum(1 / (60 + rank_i)). Query intent analysis dynamically boosts specific passages based on user question framing.", bullet_style))
    story.append(Paragraph("• <b>Grounded Anti-Hallucination Prompt:</b> Injects the top-k retrieved snippets into a strictly bounded system prompt: 'Answer using ONLY the retrieved document context. State if information is missing.'", bullet_style))
    story.append(Paragraph("• <b>Gemini LLM Synthesis:</b> Invokes Google Gemini (gemini-3.8-flash) via official google-genai SDK, outputting clear grounded answers with verified clickable source passages.", bullet_style))
    story.append(Paragraph("• <b>Resilient Offline Fallback:</b> If a network or DNS blip occurs, Clarifile automatically falls back to an offline rule-based extractor so the user still receives relevant answers directly from indexed passages.", bullet_style))

    # Section 5: Multi-Tenant Architecture & Account Security
    story.append(Paragraph("5. Multi-Tenant Architecture & Account Security", h1_style))
    story.append(Paragraph(
        "To allow safe sharing over local networks without cross-user data leakage, Clarifile enforces strict multi-tenancy:",
        body_style,
    ))
    story.append(Paragraph("• <b>PBKDF2-HMAC-SHA256 Password Security:</b> Cryptographic password hashing with 100,000 iterations and 32-byte cryptographically secure random salts. Passwords are never stored in plaintext.", bullet_style))
    story.append(Paragraph("• <b>Per-User ChromaDB Collections:</b> Each registered user receives an isolated collection named user_{username}_kb. Vectors, metadata, and chunk text are partitioned at the database storage layer.", bullet_style))
    story.append(Paragraph("• <b>Authentication Gate:</b> Unauthenticated sessions are intercepted and restricted to the Sign In / Sign Up interface, preventing unauthorized reads or queries.", bullet_style))
    story.append(Paragraph("• <b>Session State Segregation:</b> Streamlit session state is completely separated per connection. Uploads, chat history, and document libraries in one tab do not affect other connected clients.", bullet_style))

    # Section 6: UI/UX Engineering
    story.append(Paragraph("6. UI/UX Design System (Apple / Google Standard)", h1_style))
    story.append(Paragraph(
        "Clarifile features a clean, professional aesthetic tailored to both productivity and elegance:",
        body_style,
    ))
    story.append(Paragraph("• <b>Dynamic Theme Engine:</b> Instant switching between Clean Light Mode (#F8FAFC, crisp borders, dark text) and Dark Mode (#0F172A, slate cards, high-contrast light text).", bullet_style))
    story.append(Paragraph("• <b>Container Box Outlines:</b> Metric cards and Quick Action boxes feature bordered containers with action buttons enclosed cleanly inside the cards.", bullet_style))
    story.append(Paragraph("• <b>BaseWeb Dropdown Customization:</b> Custom CSS overrides prevent dark popovers from inheriting system dark mode improperly, ensuring 100% legibility in all dropdowns.", bullet_style))
    story.append(Paragraph("• <b>Tight Alignment & Dividers:</b> Document cards feature tight grouping between title and file type pills, separated from page counts by a crisp vertical divider line.", bullet_style))

    # Section 7: File Structure Reference
    story.append(Paragraph("7. File Map & Codebase Organization", h1_style))
    file_data = [
        [Paragraph("File Path", th_style), Paragraph("Module Role", th_style), Paragraph("Key Features", th_style)],
        [Paragraph("app.py", td_style), Paragraph("Main Application Router", td_style), Paragraph("Auth gate, theme engine, per-user session wiring, sidebar.", td_style)],
        [Paragraph("services/auth_service.py", td_style), Paragraph("Authentication Engine", td_style), Paragraph("SQLite credential management, PBKDF2 hashing, tenant naming.", td_style)],
        [Paragraph("components/auth_ui.py", td_style), Paragraph("Sign In & Register UI", td_style), Paragraph("Centered Apple/Google-standard authentication card.", td_style)],
        [Paragraph("services/document_loader.py", td_style), Paragraph("Document Parser", td_style), Paragraph("PDF, DOCX, XLSX, PAGES (Snappy Protobuf), CSV, TXT.", td_style)],
        [Paragraph("services/chunking.py", td_style), Paragraph("Recursive Chunker", td_style), Paragraph("Sentence-aware chunking (800 chars target, 150 overlap).", td_style)],
        [Paragraph("services/embedding_service.py", td_style), Paragraph("Dense Embedder", td_style), Paragraph("SentenceTransformers all-MiniLM-L6-v2 (384-d vectors).", td_style)],
        [Paragraph("services/vector_store.py", td_style), Paragraph("Vector Store Wrapper", td_style), Paragraph("ChromaDB persistent client, per-user collections, batch upsert.", td_style)],
        [Paragraph("services/retrieval_service.py", td_style), Paragraph("Hybrid Retrieval Engine", td_style), Paragraph("Dense cosine + Okapi BM25 with Reciprocal Rank Fusion.", td_style)],
        [Paragraph("services/rag_pipeline.py", td_style), Paragraph("RAG Synthesis Pipeline", td_style), Paragraph("Context building, anti-hallucination prompt, citation mapping.", td_style)],
        [Paragraph("services/llm_service.py", td_style), Paragraph("Gemini LLM Gateway", td_style), Paragraph("Google Gen AI SDK wrapper, fallback chain (3.8 -> 3.5 -> latest).", td_style)],
        [Paragraph("services/summarization_service.py", td_style), Paragraph("Summarization Engine", td_style), Paragraph("Executive short summary, detailed breakdown, key observations.", td_style)],
        [Paragraph("services/comparison_service.py", td_style), Paragraph("Document Comparison", td_style), Paragraph("Dual-document contrastive analysis, topic overlap matrices.", td_style)],
        [Paragraph("tests/test_rag_pipeline.py", td_style), Paragraph("RAG Test Suite", td_style), Paragraph("25 automated tests covering ingestion, chunking, RAG, mocks.", td_style)],
        [Paragraph("tests/test_auth_service.py", td_style), Paragraph("Auth Test Suite", td_style), Paragraph("7 automated tests verifying hashing, registration, isolation.", td_style)],
    ]
    ft = Table(file_data, colWidths=[150, 140, 240])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(ft)

    doc.build(story)
    print(f"PDF documentation created successfully: {filename}")


def build_docx(filename: str):
    """Generate a clean, high-standard Word (.docx) document."""
    doc = docx.Document()

    # Set standard margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(2)
    run_title = p_title.add_run("Clarifile — Intelligent File Analyzer")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("Comprehensive Technical Architecture, Tech Stack & System Workflows")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(12)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(16)
    run_meta = p_meta.add_run("Version: 1.0 Production  |  Framework: Modular RAG & Document Intelligence  |  Date: November 2026")
    run_meta.font.size = Pt(9.5)
    run_meta.font.italic = True
    run_meta.font.color.rgb = RGBColor(71, 85, 105)

    # Section 1
    doc.add_heading("1. Executive Overview & Mission", level=1)
    doc.add_paragraph(
        "Clarifile is a production-grade, modular Document Intelligence and Retrieval-Augmented Generation (RAG) platform. "
        "It solves information silos by transforming heterogeneous multi-format files into mathematically indexed vector spaces, "
        "allowing authenticated users to converse with their files, extract multi-tier executive summaries, and perform comparative "
        "side-by-side technical analyses. Each user account operates in a completely isolated sandbox with dedicated vector collections, "
        "preventing data leakage across users."
    )

    # Section 2
    doc.add_heading("2. Tools & Technology Stack", level=1)
    tech_data = [
        ("Category", "Technology / Library", "Specification", "Role in System"),
        ("Frontend UI", "Streamlit", "1.35+", "Reactive web interface, reactive session routing, BaseWeb UI styling."),
        ("Dense Vectors", "SentenceTransformers", "all-MiniLM-L6-v2", "384-dimensional dense semantic embeddings with L2 normalization."),
        ("Vector Database", "ChromaDB", "Persistent HNSW", "Cosine similarity vector store with isolated per-user collections."),
        ("Keyword Search", "Rank-BM25", "Okapi BM25", "Exact lexical keyword matching for technical codes, names, and metrics."),
        ("Rank Fusion", "RRF Algorithm", "k=60 Fusion", "Harmonizes dense semantic and lexical sparse rankings with intent boost."),
        ("Generative LLM", "Google Gemini API", "gemini-3.8-flash", "Grounded contextual reasoning, verified citations, executive summaries."),
        ("Multi-Format Parsers", "PyPDF2, docx, openpyxl, snappy", "Custom parsers", "Parses PDF, DOCX, XLSX, CSV, TXT, and Apple Pages (.pages) archives."),
        ("Authentication", "SQLite3 + hashlib", "PBKDF2-HMAC-SHA256", "100,000 rounds, 32-byte salts, unique usernames, tenant isolation."),
        ("Test Suite", "pytest", "32 Tests (100%)", "Automated unit and integration testing across all RAG and auth flows."),
    ]
    t = doc.add_table(rows=len(tech_data), cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(tech_data):
        for c_idx, val in enumerate(row):
            cell = t.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            if r_idx == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(9)
            else:
                p.runs[0].font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Section 3
    doc.add_heading("3. Document Ingestion Pipeline Flow", level=1)
    doc.add_paragraph(
        "When a document is uploaded, it transitions through a strictly validated 4-stage pipeline:"
    )
    doc.add_paragraph("• Extraction (DocumentLoader): Inspects file binary signatures. For Apple Pages, extracts embedded QuickLook PDFs or decompresses raw Snappy Protobuf .iwa frames. For PDFs, extracts page text. For DOCX, iterates paragraphs and table cells. For Excel/CSV, extracts cell values with sheet metadata.")
    doc.add_paragraph("• Sentence-Aware Chunking (ChunkingService): Splits extracted text into semantic passages of 800 characters with 150 characters overlap. Boundaries prioritize punctuation to prevent fragmented sentences. Every chunk retains document ID, filename, and page number.")
    doc.add_paragraph("• Dense Vectorization (EmbeddingService): Batch-vectorizes chunk text via all-MiniLM-L6-v2 into 384-dimensional floating-point vectors normalized to unit length.")
    doc.add_paragraph("• Isolated Indexing (VectorStore): Inserts embeddings and chunk metadata into the user's private ChromaDB collection (user_{username}_kb) in batches of 250 records.")

    # Section 4
    doc.add_heading("4. Hybrid Retrieval & Grounded RAG Flow", level=1)
    doc.add_paragraph(
        "Clarifile avoids the common failure modes of pure dense search by utilizing a state-of-the-art Hybrid Search architecture:"
    )
    doc.add_paragraph("• Dense Retrieval: Queries ChromaDB using HNSW cosine distance to find conceptually related chunks.")
    doc.add_paragraph("• Sparse Okapi BM25: Computes term-frequency inverse-document-frequency keyword relevance across all indexed chunks in the active scope.")
    doc.add_paragraph("• Reciprocal Rank Fusion (RRF): Aggregates both ranked candidate sets using RRF(d) = sum(1 / (60 + rank_i)). Query intent analysis dynamically boosts specific passages based on user question framing.")
    doc.add_paragraph("• Grounded Anti-Hallucination Prompt: Injects the top-k retrieved snippets into a strictly bounded system prompt: 'Answer using ONLY the retrieved document context. State if information is missing.'")
    doc.add_paragraph("• Gemini LLM Synthesis: Invokes Google Gemini (gemini-3.8-flash) via official google-genai SDK, outputting clear grounded answers with verified clickable source passages.")
    doc.add_paragraph("• Resilient Offline Fallback: If a network or DNS blip occurs, Clarifile automatically falls back to an offline rule-based extractor so the user still receives relevant answers directly from indexed passages.")

    # Section 5
    doc.add_heading("5. Multi-Tenant Architecture & Account Security", level=1)
    doc.add_paragraph(
        "To allow safe sharing over local networks without cross-user data leakage, Clarifile enforces strict multi-tenancy:"
    )
    doc.add_paragraph("• PBKDF2-HMAC-SHA256 Password Security: Cryptographic password hashing with 100,000 iterations and 32-byte cryptographically secure random salts.")
    doc.add_paragraph("• Per-User ChromaDB Collections: Each registered user receives an isolated collection named user_{username}_kb. Vectors, metadata, and chunk text are partitioned at the database storage layer.")
    doc.add_paragraph("• Authentication Gate: Unauthenticated sessions are intercepted and restricted to the Sign In / Sign Up interface, preventing unauthorized reads or queries.")
    doc.add_paragraph("• Session State Segregation: Streamlit session state is completely separated per connection. Uploads, chat history, and document libraries in one tab do not affect other connected clients.")

    # Section 6
    doc.add_heading("6. UI/UX Design System (Apple / Google Standard)", level=1)
    doc.add_paragraph(
        "Clarifile features a clean, professional aesthetic tailored to both productivity and elegance:"
    )
    doc.add_paragraph("• Dynamic Theme Engine: Instant switching between Clean Light Mode (#F8FAFC, crisp borders, dark text) and Dark Mode (#0F172A, slate cards, high-contrast light text).")
    doc.add_paragraph("• Container Box Outlines: Metric cards and Quick Action boxes feature bordered containers with action buttons enclosed cleanly inside the cards.")
    doc.add_paragraph("• BaseWeb Dropdown Customization: Custom CSS overrides prevent dark popovers from inheriting system dark mode improperly, ensuring 100% legibility in all dropdowns.")
    doc.add_paragraph("• Tight Alignment & Dividers: Document cards feature tight grouping between title and file type pills, separated from page counts by a crisp vertical divider line.")

    # Section 7
    doc.add_heading("7. File Map & Codebase Organization", level=1)
    file_data = [
        ("File Path", "Module Role", "Key Features"),
        ("app.py", "Main Application Router", "Auth gate, theme engine, per-user session wiring, sidebar."),
        ("services/auth_service.py", "Authentication Engine", "SQLite credential management, PBKDF2 hashing, tenant naming."),
        ("components/auth_ui.py", "Sign In & Register UI", "Centered Apple/Google-standard authentication card."),
        ("services/document_loader.py", "Document Parser", "PDF, DOCX, XLSX, PAGES (Snappy Protobuf), CSV, TXT."),
        ("services/chunking.py", "Recursive Chunker", "Sentence-aware chunking (800 chars target, 150 overlap)."),
        ("services/embedding_service.py", "Dense Embedder", "SentenceTransformers all-MiniLM-L6-v2 (384-d vectors)."),
        ("services/vector_store.py", "Vector Store Wrapper", "ChromaDB persistent client, per-user collections, batch upsert."),
        ("services/retrieval_service.py", "Hybrid Retrieval Engine", "Dense cosine + Okapi BM25 with Reciprocal Rank Fusion."),
        ("services/rag_pipeline.py", "RAG Synthesis Pipeline", "Context building, anti-hallucination prompt, citation mapping."),
        ("services/llm_service.py", "Gemini LLM Gateway", "Google Gen AI SDK wrapper, fallback chain (3.8 -> 3.5 -> latest)."),
        ("services/summarization_service.py", "Summarization Engine", "Executive short summary, detailed breakdown, key observations."),
        ("services/comparison_service.py", "Document Comparison", "Dual-document contrastive analysis, topic overlap matrices."),
        ("tests/test_rag_pipeline.py", "RAG Test Suite", "25 automated tests covering ingestion, chunking, RAG, mocks."),
        ("tests/test_auth_service.py", "Auth Test Suite", "7 automated tests verifying hashing, registration, isolation."),
    ]
    ft = doc.add_table(rows=len(file_data), cols=3)
    ft.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(file_data):
        for c_idx, val in enumerate(row):
            cell = ft.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            if r_idx == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(9)
            else:
                p.runs[0].font.size = Pt(8.5)

    doc.save(filename)
    print(f"DOCX documentation created successfully: {filename}")


if __name__ == "__main__":
    out_dir = "/Users/midhundg/Clarifile"
    pdf_path = os.path.join(out_dir, "Clarifile_Complete_System_Documentation.pdf")
    docx_path = os.path.join(out_dir, "Clarifile_Complete_System_Documentation.docx")
    build_pdf(pdf_path)
    build_docx(docx_path)
