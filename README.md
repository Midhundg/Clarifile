# Clarifile – AI Document Intelligence System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Sentence Transformers](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20GenAI%20Gemini%203.8%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Tests Passing](https://img.shields.io/badge/Tests-32%2F32%20Passing-brightgreen.svg)](tests/)
[![Multi-User](https://img.shields.io/badge/Security-Multi--Tenant%20Auth-success.svg)](services/auth_service.py)

---

## 1. Project Overview

**Clarifile** is an enterprise-grade, production-quality RAG (Retrieval-Augmented Generation) Document Intelligence System. Originally created as a rule-based file analyzer, Clarifile has been completely transformed into a modern, multi-user, service-oriented platform that extracts, cleans, chunks, embeds, persists, and performs semantic question-answering across multi-format business and research documents.

Clarifile bridges the gap between raw unstructured document silos (PDF, DOCX, Apple Pages, TXT, CSV, XLSX) and actionable intelligence. It guarantees **factual grounding** by enforcing strict context boundaries on Large Language Models, eliminating hallucinations, providing verified source citations down to the exact document and page/sheet level, and isolating data between different user accounts.

---

## 2. Key Capabilities & Features

- **Multi-Tenant User Accounts & Isolation**: Full SQLite-backed authentication with PBKDF2-HMAC-SHA256 password cryptography (100k rounds, 32-byte salts). Each user receives an isolated ChromaDB vector collection (`user_{username}_kb`), guaranteeing zero data leakage when sharing localhost or network URLs.
- **Multi-Format Document Ingestion**: Native extraction for **PDF** (page-by-page), **DOCX** (paragraphs and tables), **Apple Pages (.pages)** (QuickLook preview + 24-bit Snappy Protobuf frame decompressor), **TXT** (auto-encoding), **CSV**, and **Excel XLSX** (multi-worksheet support).
- **Sentence-Aware Recursive Chunking**: Configurable chunk size (default: 800 characters) and overlap (default: 150 characters) designed to preserve semantic context and prevent mid-sentence truncation.
- **Dense Vector Embeddings**: High-efficiency 384-dimensional vector embeddings generated using `sentence-transformers/all-MiniLM-L6-v2` with local cache fallback and batch encoding.
- **Persistent Vector Database**: Embedded ChromaDB vector storage with HNSW cosine distance metric persisted locally per user.
- **Hybrid Retrieval & Reciprocal Rank Fusion (RRF)**: Combines dense semantic vector search with sparse Okapi BM25 keyword matching using reciprocal rank fusion ($k=60$) and query intent boosting.
- **Grounded LLM Question Answering**: Integrated with Google Gen AI SDK (`google-genai`) using `gemini-3.8-flash` with automatic fallback to `gemini-3.5-flash` and strict anti-hallucination system constraints.
- **Resilient Offline Fallback**: If an internet/DNS interruption occurs, the system automatically falls back to extractive heuristics from indexed passages so queries never fail with raw socket errors.
- **Auditable Source Citations**: Real-time display of retrieved chunk passages, document file names, page numbers, and similarity relevance scores.
- **Intelligent Multi-Tier Summarization**: Short summary (executive 2-3 sentences), detailed structured summary, and important observations, with map-reduce section chunking for large files.
- **Dual-Document Comparative Intelligence**: Side-by-side contrastive analysis of two documents evaluating main topics, similarities, differences, omissions, and keyword vocabulary overlap.
- **Minimalist Light & Dark Mode UI**: Apple/Google-standard clean UI with dynamic contrast tokens, container-box card outlines, and BaseWeb popover styling.
- **Downloadable System Documentation**: Built-in generators for professional **PDF** and **Word DOCX** system documentation with one-click in-app downloads.

---

## 3. Architecture

Clarifile adheres to a modular, service-oriented architecture separating data extraction, transformation, embedding, vector storage, retrieval, synthesis, and UI presentation:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Streamlit Frontend Layer                              │
│   [Dashboard]   [Document Library]   [AI Chat]   [Analysis]   [Comparison]      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────┐
│                             Service Orchestration Layer                         │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐│
│  │   DocumentLoader      │  │   TextProcessor       │  │   ChunkingService     ││
│  │  (PDF,DOCX,TXT,CSV,XLS)│  │ (Clean, Segment, Stats)│  │ (Sentence, Overlap)   ││
│  └───────────┬───────────┘  └───────────────────────┘  └───────────┬───────────┘│
│              │                                                     │            │
│  ┌───────────▼───────────┐  ┌───────────────────────┐  ┌───────────▼───────────┐│
│  │   EmbeddingService    │  │   VectorStore         │  │   RetrievalService    ││
│  │  (SentenceTransformer)│◄─┼─ (ChromaDB Persistent)│◄─┼─  (Cosine Top-K)      ││
│  └───────────────────────┘  └───────────────────────┘  └───────────┬───────────┘│
│                                                                    │            │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────▼───────────┐│
│  │ SummarizationService  │  │   KeywordService      │  │     RAGPipeline       ││
│  │ (Short, Detail, Obs)  │  │   (TF-IDF N-Grams)    │  │  (Grounded Synthesis) ││
│  └───────────┬───────────┘  └───────────────────────┘  └───────────┬───────────┘│
│              │                                                     │            │
│              └──────────────────────────┬──────────────────────────┘            │
│                                         │                                       │
│                             ┌───────────▼───────────┐                           │
│                             │     LLMService        │                           │
│                             │   (Google Gemini)     │                           │
│                             └───────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **UI / Frontend** | Streamlit (>= 1.40.0) | Interactive SaaS web application |
| **Language** | Python 3.10+ | Core application backend |
| **Document Processing** | PyPDF2, python-docx, pandas, openpyxl | Multi-format extraction (PDF, DOCX, TXT, CSV, XLSX) |
| **Text Processing** | Regular Expressions, unicodedata, scikit-learn | Normalization, sentence segmentation, TF-IDF |
| **Embedding Model** | Sentence Transformers (`all-MiniLM-L6-v2`) | Dense 384-dimensional vector embeddings |
| **Vector Database** | ChromaDB (>= 0.5.0) | Persistent local vector storage and indexing |
| **LLM Provider** | Google Gen AI SDK (`google-genai` / Gemini 2.5 Flash) | Contextual question answering & analysis |
| **Configuration** | python-dotenv, Pydantic | Environment management and data validation |
| **Testing** | pytest (>= 8.0.0) | Automated unit and integration test suite |

---

## 5. Project Folder Structure

```
Clarifile/
│
├── app.py                      # Primary Streamlit application entry point
├── Clarifile.py                # Backward-compatibility runner
├── requirements.txt            # Application dependencies
├── .env.example                # Example environment configuration template
├── .gitignore                  # Git ignore rules for virtualenv, ChromaDB, secrets
├── README.md                   # Complete architectural and operational documentation
│
├── services/                   # Modular backend business logic
│   ├── __init__.py
│   ├── document_loader.py      # Extractor for PDF, DOCX, TXT, CSV, XLSX
│   ├── text_processor.py       # Cleaning, normalization, sentence boundary detection
│   ├── chunking.py             # Sentence-aware overlapping chunker
│   ├── embedding_service.py    # SentenceTransformer model wrapper with batching
│   ├── vector_store.py         # Persistent ChromaDB client and collection manager
│   ├── retrieval_service.py    # Cosine similarity retrieval with threshold filtering
│   ├── llm_service.py          # Modular Google Gen AI SDK integration & test mock
│   ├── rag_pipeline.py         # End-to-end RAG orchestrator with verified citations
│   ├── summarization_service.py# Multi-tier summarizer with map-reduce support
│   ├── keypoint_service.py     # Grounded key points, facts, decisions, and dates
│   ├── keyword_service.py      # TF-IDF statistical unigram and bigram extraction
│   └── comparison_service.py   # Multi-document comparative intelligence
│
├── components/                 # Streamlit UI page components
│   ├── __init__.py
│   ├── dashboard.py            # Overview dashboard, operational metrics, quick actions
│   ├── document_library.py     # Upload, ingestion progress, table, preview, deletion
│   ├── chat_interface.py       # RAG chat, scope filter, citations, chunk inspection
│   ├── document_analysis.py    # Summaries, key points, TF-IDF keywords, statistics
│   └── document_comparison.py  # Side-by-side contrastive document analysis
│
├── utils/                      # Utilities and helpers
│   ├── __init__.py
│   ├── config.py               # Centralized settings and environment variables
│   ├── validators.py           # File validation, size checks, path sanitization
│   └── helpers.py              # Content hashing, file formatting, citation builders
│
├── data/                       # Local data persistence
│   ├── .gitkeep
│   └── chroma_db/              # Persistent ChromaDB vector index directory (gitignored)
│
└── tests/                      # Automated test suite (22 tests)
    ├── __init__.py
    ├── test_document_loader.py # Tests for all 5 document loaders and error handling
    ├── test_chunking.py        # Tests for chunk sizes, overlap, and sentence bounds
    ├── test_retrieval.py       # Tests for embeddings, ChromaDB, search, and deletion
    └── test_rag_pipeline.py    # Tests for RAG answers, citations, fallback modes
```

---

## 6. Installation Instructions

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed on your system.
- Git.

### Clone and Enter Directory
```bash
git clone <repository_url>
cd Clarifile
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. Virtual Environment Setup

It is strongly recommended to install and run Clarifile inside an isolated Python virtual environment:

### macOS / Linux
```bash
# 1. Create a virtual environment using Python 3.10 - 3.12
python3 -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. Environment Variable Configuration

Clarifile uses `python-dotenv` to manage application configuration.

Copy the example template to create your `.env` file:
```bash
cp .env.example .env
```

Open `.env` in any text editor and adjust settings as needed:
```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini Model Selection (default: gemini-3.8-flash)
GEMINI_MODEL=gemini-3.8-flash

# Sentence Transformers Embedding Model
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Persistent ChromaDB Directory Path
CHROMA_PERSIST_DIR=data/chroma_db

# ChromaDB Collection Name
CHROMA_COLLECTION_NAME=clarifile_documents

# Chunking Configuration
DEFAULT_CHUNK_SIZE=800
DEFAULT_CHUNK_OVERLAP=150

# Retrieval Configuration
DEFAULT_TOP_K=5
SIMILARITY_THRESHOLD=0.25

# File Size Restriction in MB
MAX_FILE_SIZE_MB=25
```

---

## 9. How to Obtain and Configure a Gemini API Key

Clarifile uses the modern Google Gen AI SDK to communicate with Gemini models.

1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click on **Get API key** and select **Create API key**.
4. Copy the generated key.
5. You can configure your key in either of two ways:
   - **Method A (Persistent)**: Paste it into your `.env` file under `GEMINI_API_KEY=your_key`.
   - **Method B (Runtime)**: Enter it directly into the password field in the Clarifile sidebar inside the web app. The key is securely preserved for your session.

*Note: If no API key is supplied, Clarifile still functions for document parsing, chunking, vector indexing, semantic search, TF-IDF keyword extraction, and extractive rule-based summaries. Gemini-specific RAG generation will prompt you to provide an API key.*

---

## 10. How to Run the Application

With your virtual environment activated:

```bash
streamlit run app.py
```

The application will start and open in your default browser at:
```
http://localhost:8501
```

*(Alternatively, running `streamlit run Clarifile.py` will automatically execute the system.)*

---

## 11. How the RAG Pipeline Works

```
 User Question ──► Query Embedding (all-MiniLM-L6-v2)
                          │
                          ▼
                  Cosine Similarity
                   Search (ChromaDB)
                          │
                          ▼
                   Top-K Filtering
               (Threshold >= 0.25)
                          │
                          ▼
            Context Assembly with Exact Citations
            [Source 1: File A, Page 2] Chunk text...
            [Source 2: File B, Page 5] Chunk text...
                          │
                          ▼
                  Google Gemini LLM
            (Strictly Grounded System Prompt)
                          │
                          ▼
             Final Answer with Verified Citations
```

1. **Document Ingestion**: The user uploads files. The `DocumentLoader` parses pages and tables, retaining page numbers and worksheet names.
2. **Chunking**: `ChunkingService` groups sentences into ~800-character blocks with 150-character overlaps.
3. **Embedding**: `EmbeddingService` encodes each chunk using `all-MiniLM-L6-v2` into a normalized 384-dimensional vector.
4. **Vector Storage**: `VectorStore` persists chunk vectors, texts, and source metadata into local ChromaDB storage.
5. **Question Embedding**: When a user submits a prompt, Clarifile embeds the inquiry using the same model.
6. **Retrieval**: `RetrievalService` runs cosine similarity search in ChromaDB, retrieves the top-K chunks, and filters out candidates below the similarity threshold.
7. **Prompt Construction**: Chunks are assembled into a formatted context block where each passage is explicitly labeled with its file name and page number.
8. **Grounded Generation**: Gemini processes the question under strict instructions to rely exclusively on the retrieved passages and not hallucinate external facts.
9. **Citation Inspection**: The user receives the answer alongside an interactive expander displaying the exact source passages and relevance scores.

---

## 12. Example Questions

Once documents are indexed, try asking questions such as:

### Specific Fact Extraction
> *"What is the total quarterly revenue reported for Q3, and what was the percentage growth compared to Q2?"*

### Cross-Document Synthesis
> *"Based on both the technical architecture PDF and the project roadmap DOCX, what are the primary milestones scheduled for Q4?"*

### Action Item & Decision Tracking
> *"What specific recommendations or decisions were approved regarding database migration?"*

### Procedural Inquiries
> *"What steps are outlined in the manual to reboot the server rack safely?"*

### Handling Unsupported Queries (Groundedness Test)
> *"What is the capital of Mars?"*
> *(Clarifile will accurately respond: 'The information was not found in the uploaded documents.')*

---

## 13. Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `GEMINI_API_KEY is not configured` | API key is missing from `.env` or sidebar | Obtain an API key from Google AI Studio and enter it in the sidebar or `.env`. |
| `Unsupported document format` | File has an unsupported extension | Upload PDF, DOCX, TXT, CSV, or XLSX files only. |
| `File is empty (0 bytes)` | File contains no data | Ensure the uploaded file has content. |
| `PDF contains no extractable text` | PDF contains only scanned raster images | Clarifile processes digital text PDFs. OCR integration can be added for scanned documents. |
| `PermissionError on ~/.streamlit` | Running in a restricted environment | Set `HOME=$(pwd)` or ensure write access to your user home directory. |
| `ChromaDB vector error` | Corrupted index directory | Click **Reset All Documents** in the Document Library or remove `data/chroma_db/`. |

---

## 14. Future Enhancements

- [ ] **OCR Ingestion**: Tesseract / Google Vision OCR support for scanned image-only PDFs.
- [ ] **Hybrid Search**: Combine BM25 keyword search with dense vector embeddings (Reciprocal Rank Fusion).
- [ ] **Reranking**: Integrate cross-encoder rerankers (e.g. `bge-reranker-base`) for higher precision retrieval.
- [ ] **Multi-Modal Analysis**: Extract and summarize embedded diagrams, charts, and images inside PDF documents.
- [ ] **Additional LLM Providers**: Plug-and-play adapter support for Anthropic Claude, OpenAI, and local Ollama models.
- [ ] **Streaming Responses**: Real-time token streaming for chat generation in Streamlit.
- [ ] **User Authentication & Multi-Tenancy**: Workspace isolation with PostgreSQL-backed vector partitions.

---

## 15. Running Automated Tests

Clarifile includes a comprehensive automated test suite with 22 tests covering extractors, chunkers, embedding generation, ChromaDB vector storage, semantic search, grounded RAG synthesis, error handling, and document deletion:

```bash
# Run the complete test suite
pytest tests/ -v
```

All tests utilize mocked LLM responses so that tests run deterministically offline without incurring API charges.
