"""Clarifile — Production-Grade AI Document Intelligence System.

RAG-powered multi-document analysis, semantic retrieval, and contextual generation.
"""

import streamlit as st
from utils.config import Config
from services.chunking import ChunkingService
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.retrieval_service import RetrievalService
from services.llm_service import GeminiLLMService
from services.rag_pipeline import RAGPipeline
from services.summarization_service import SummarizationService
from services.keypoint_service import KeyPointService
from services.comparison_service import ComparisonService
from services.document_loader import ExtractedDocument, DocumentPage
from services.auth_service import AuthService

from components.dashboard import render_dashboard
from components.document_library import render_document_library
from components.chat_interface import render_chat_interface
from components.document_analysis import render_document_analysis
from components.document_comparison import render_document_comparison
from components.auth_ui import render_auth_page

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Clarifile – Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Theme & Palette Definitions (Clean Light with Crisp Attractive Outlines)
# -----------------------------------------------------------------------------
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "Light"

THEMES = {
    "Light": {
        "bg_app": "#F8FAFC",
        "bg_surface": "#FFFFFF",
        "bg_sidebar": "#FFFFFF",
        "bg_pill": "#F1F5F9",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "border": "#CBD5E1",
        "border_focus": "#94A3B8",
        "accent": "#0066CC",
        "accent_hover": "#0052A3",
        "accent_light": "#EFF6FF",
    },
    "Dark": {
        "bg_app": "#0F172A",
        "bg_surface": "#1E293B",
        "bg_sidebar": "#0F172A",
        "bg_pill": "#334155",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "border": "#334155",
        "border_focus": "#60A5FA",
        "accent": "#3B82F6",
        "accent_hover": "#2563EB",
        "accent_light": "rgba(59, 130, 246, 0.15)",
    },
}

current_theme_name = st.session_state.get("ui_theme", "Light")
if current_theme_name not in THEMES:
    current_theme_name = "Light"
    st.session_state.ui_theme = "Light"

current_palette = THEMES[current_theme_name]

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: {current_palette["text_primary"]};
    }}

    .stApp {{
        background-color: {current_palette["bg_app"]} !important;
    }}

    /* Transparent top header bar (removes dark stripe) */
    header[data-testid="stHeader"], [data-testid="stHeader"], [data-testid="stAppHeader"], .stAppHeader {{
        background-color: transparent !important;
        background: transparent !important;
        box-shadow: none !important;
    }}
    header[data-testid="stHeader"] button, header[data-testid="stHeader"] svg {{
        color: {current_palette["text_secondary"]} !important;
        fill: {current_palette["text_secondary"]} !important;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1150px;
    }}

    h1, h2, h3, h4 {{
        font-weight: 700;
        color: {current_palette["text_primary"]} !important;
        letter-spacing: -0.02em;
    }}

    p, span, label, div {{
        color: {current_palette["text_primary"]};
    }}

    /* Native Container Box Outlines (Proper Outlines for Every Box) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {{
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 12px !important;
        background-color: {current_palette["bg_surface"]} !important;
        padding: 18px 20px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div:first-child:hover {{
        border-color: {current_palette["border_focus"]} !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
    }}

    /* Metrics with Crisp Borders */
    div[data-testid="stMetric"] {{
        background: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }}
    div[data-testid="stMetric"] label {{
        color: {current_palette["text_secondary"]} !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {current_palette["text_primary"]} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        white-space: normal !important;
        overflow: visible !important;
        word-break: break-word !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: {current_palette["bg_surface"]};
        color: {current_palette["text_primary"]};
        border: 1.5px solid {current_palette["border"]};
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        background: {current_palette["bg_pill"]};
        border-color: {current_palette["border_focus"]};
    }}
    .stButton > button[kind="primary"] {{
        background: {current_palette["accent"]} !important;
        color: #FFFFFF !important;
        border: 1.5px solid {current_palette["accent"]} !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    .stButton > button[kind="primary"]:hover {{
        background: {current_palette["accent_hover"]} !important;
        border-color: {current_palette["accent_hover"]} !important;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {current_palette["bg_sidebar"]} !important;
        border-right: 1.5px solid {current_palette["border"]} !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: {current_palette["bg_pill"]} !important;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
        border: 1px solid {current_palette["border"]};
        margin-bottom: 18px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: 500;
        font-size: 0.88rem;
        color: {current_palette["text_secondary"]};
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {current_palette["bg_surface"]} !important;
        color: {current_palette["accent"]} !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 10px !important;
        box-shadow: none;
    }}

    /* Inputs & Selectboxes */
    div[data-baseweb="select"] {{
        background-color: {current_palette["bg_surface"]} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{
        background: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] [aria-selected] {{
        color: {current_palette["text_primary"]} !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: {current_palette["text_secondary"]} !important;
    }}

    /* Dropdown Menus, Selectbox Option Lists & Popovers */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-baseweb="menu"],
    ul[role="listbox"],
    div[data-testid="stSelectboxVirtualDropdown"] {{
        background-color: {current_palette["bg_surface"]} !important;
        background: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    }}

    li[data-baseweb="menu-item"],
    li[role="option"],
    div[role="option"] {{
        background-color: {current_palette["bg_surface"]} !important;
        color: {current_palette["text_primary"]} !important;
        font-size: 0.9rem !important;
        padding: 8px 14px !important;
        cursor: pointer !important;
    }}

    li[data-baseweb="menu-item"]:hover,
    li[role="option"]:hover,
    li[aria-selected="true"],
    li[data-baseweb="menu-item"][aria-selected="true"],
    li[role="option"][aria-selected="true"] {{
        background-color: {current_palette["accent_light"]} !important;
        color: {current_palette["accent"]} !important;
    }}

    /* Text inside dropdown items */
    div[data-baseweb="popover"] span,
    div[data-baseweb="popover"] div,
    ul[data-baseweb="menu"] span,
    ul[data-baseweb="menu"] div,
    ul[role="listbox"] span,
    ul[role="listbox"] div,
    li[role="option"] span,
    li[role="option"] div {{
        color: {current_palette["text_primary"]} !important;
    }}

    li[role="option"]:hover span,
    li[role="option"]:hover div,
    li[role="option"][aria-selected="true"] span,
    li[role="option"][aria-selected="true"] div,
    li[data-baseweb="menu-item"]:hover span,
    li[data-baseweb="menu-item"]:hover div {{
        color: {current_palette["accent"]} !important;
    }}

    /* Bottom Chat Input Fixed Bar & Container */
    footer {{
        visibility: hidden;
    }}
    div[data-testid="stBottom"],
    div[data-testid="stBottom"] > div {{
        background-color: {current_palette["bg_app"]} !important;
        background: {current_palette["bg_app"]} !important;
    }}
    div[data-testid="stChatInput"] {{
        background-color: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    }}
    div[data-testid="stChatInput"]:focus-within {{
        border-color: {current_palette["border_focus"]} !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        color: {current_palette["text_primary"]} !important;
        background-color: transparent !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: {current_palette["text_secondary"]} !important;
    }}
    div[data-testid="stChatInput"] button {{
        color: {current_palette["accent"]} !important;
    }}

    /* Chat Messages Bubbles */
    div[data-testid="stChatMessage"] {{
        background-color: {current_palette["bg_surface"]} !important;
        border: 1.5px solid {current_palette["border"]} !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
    }}
    div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {{
        color: {current_palette["text_primary"]} !important;
    }}

    /* Code Tags & Badges */
    code {{
        background: {current_palette["bg_pill"]} !important;
        color: {current_palette["text_primary"]} !important;
        border: 1px solid {current_palette["border"]} !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
        font-size: 0.85em !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# User Authentication Gate
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_auth_service() -> AuthService:
    svc = AuthService()
    svc.seed_default_user_if_empty()
    return svc


auth_service = get_auth_service()

if "authenticated_user" not in st.session_state or not st.session_state.authenticated_user:
    render_auth_page(auth_service)
    st.stop()

current_user = st.session_state.authenticated_user
user_collection = AuthService.sanitize_collection_name(current_user["username"])

# -----------------------------------------------------------------------------
# Per-User Service Initialization & Session State Management
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_user_vector_store(collection_name: str) -> VectorStore:
    """Instantiate and cache a dedicated ChromaDB collection for each user."""
    return VectorStore(collection_name=collection_name)


@st.cache_resource(show_spinner=False)
def get_shared_nlp_services():
    """Instantiate shared Sentence Transformer embedding model and chunker."""
    embedding_service = EmbeddingService.get_instance()
    chunking_service = ChunkingService(
        chunk_size=Config.DEFAULT_CHUNK_SIZE,
        chunk_overlap=Config.DEFAULT_CHUNK_OVERLAP,
    )
    return embedding_service, chunking_service


vector_store = get_user_vector_store(user_collection)
embedding_service, chunking_service = get_shared_nlp_services()
retrieval_service = RetrievalService(
    vector_store=vector_store,
    embedding_service=embedding_service,
)

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = Config.GEMINI_API_KEY


# Restore persisted documents from ChromaDB if user session library is empty
def restore_persisted_documents():
    if not st.session_state.uploaded_docs and vector_store.get_total_chunks() > 0:
        try:
            records = vector_store.collection.get(include=["documents", "metadatas"])
            if records and records["ids"]:
                doc_groups = {}
                for text, meta in zip(records["documents"], records["metadatas"]):
                    d_id = meta.get("doc_id")
                    if not d_id:
                        continue
                    if d_id not in doc_groups:
                        doc_groups[d_id] = {
                            "file_name": meta.get("file_name", "Recovered Document"),
                            "file_type": meta.get("file_type", "txt"),
                            "pages": {},
                        }
                    page_num = meta.get("page_number", "1")
                    if page_num not in doc_groups[d_id]["pages"]:
                        doc_groups[d_id]["pages"][page_num] = []
                    doc_groups[d_id]["pages"][page_num].append(text)

                for d_id, data in doc_groups.items():
                    pages = []
                    for p_num, chunks_text in data["pages"].items():
                        pages.append(
                            DocumentPage(
                                page_number=p_num,
                                text="\n\n".join(chunks_text),
                                metadata={"page_number": p_num, "file_name": data["file_name"]},
                            )
                        )
                    full_text = "\n\n".join([p.text for p in pages])
                    st.session_state.uploaded_docs[d_id] = ExtractedDocument(
                        doc_id=d_id,
                        file_name=data["file_name"],
                        file_type=data["file_type"],
                        file_size=len(full_text.encode("utf-8")),
                        pages=pages,
                        full_text=full_text,
                        metadata={"doc_id": d_id, "file_name": data["file_name"], "file_type": data["file_type"]},
                    )
        except Exception:
            pass


user_restore_key = f"docs_restored_{current_user['id']}"
if user_restore_key not in st.session_state:
    st.session_state[user_restore_key] = True
    restore_persisted_documents()

# Initialize dynamic LLM and RAG Pipeline
active_api_key = st.session_state.gemini_api_key
llm_service = GeminiLLMService(api_key=active_api_key, model=Config.GEMINI_MODEL)

rag_pipeline = RAGPipeline(
    retrieval_service=retrieval_service,
    llm_service=llm_service,
)
summarization_service = SummarizationService(llm_service=llm_service)
keypoint_service = KeyPointService(llm_service=llm_service)
comparison_service = ComparisonService(llm_service=llm_service)


# -----------------------------------------------------------------------------
# Clean Sidebar Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0 14px 0; border-bottom: 1px solid rgba(0,0,0,0.06); margin-bottom: 14px;">
            <h2 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: {current_palette['text_primary']} !important;">📄 Clarifile</h2>
            <div style="font-size: 0.82rem; color: {current_palette['text_secondary']}; margin-top: 2px;">Document Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active User Profile Badge
    avatar_char = (current_user.get("display_name") or current_user.get("username") or "U")[:1].upper()
    st.markdown(
        f"""
        <div style="
            display: flex; align-items: center; gap: 10px;
            padding: 8px 12px; margin-bottom: 14px;
            background: {current_palette['bg_pill']};
            border: 1px solid {current_palette['border']};
            border-radius: 10px;
        ">
            <div style="
                width: 34px; height: 34px; border-radius: 50%;
                background: {current_palette['accent']}; color: #FFFFFF;
                display: flex; align-items: center; justify-content: center;
                font-weight: 700; font-size: 14px; flex-shrink: 0;
            ">{avatar_char}</div>
            <div style="line-height: 1.25; overflow: hidden; flex: 1;">
                <div style="font-weight: 700; font-size: 0.88rem; color: {current_palette['text_primary']}; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">
                    {current_user.get('display_name', current_user['username'])}
                </div>
                <div style="font-size: 0.74rem; color: {current_palette['text_secondary']};">
                    @{current_user['username']}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_pages = [
        "Dashboard",
        "Document Library",
        "AI Chat",
        "Document Analysis",
        "Document Comparison",
    ]

    selected_page = st.radio(
        "Navigation",
        options=nav_pages,
        index=nav_pages.index(st.session_state.active_page) if st.session_state.active_page in nav_pages else 0,
        label_visibility="collapsed",
    )
    st.session_state.active_page = selected_page

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Theme Switcher: Only Light and Dark
    st.markdown(f"<div style='font-size: 0.78rem; font-weight: 600; color: {current_palette['text_secondary']}; margin-bottom: 6px; letter-spacing: 0.04em;'>THEME</div>", unsafe_allow_html=True)
    theme_options = ["Light", "Dark"]
    theme_idx = 0 if st.session_state.ui_theme == "Light" else 1
    chosen_theme = st.radio(
        "Theme",
        options=theme_options,
        index=theme_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio_selector",
    )
    if chosen_theme != st.session_state.ui_theme:
        st.session_state.ui_theme = chosen_theme
        st.rerun()

    st.markdown("<hr style='margin: 16px 0 12px 0; border: none; border-top: 1px solid rgba(0,0,0,0.08);'>", unsafe_allow_html=True)
    total_chunks_indexed = vector_store.get_total_chunks()
    st.caption(f"📁 {len(st.session_state.uploaded_docs)} document(s) • {total_chunks_indexed} chunks")

    # Quick Documentation Download
    pdf_doc_path = "Clarifile_Complete_System_Documentation.pdf"
    if os.path.exists(pdf_doc_path):
        with open(pdf_doc_path, "rb") as f:
            st.download_button(
                label="📥 Download System Docs (PDF)",
                data=f.read(),
                file_name="Clarifile_Complete_System_Documentation.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_sidebar_dl_pdf",
            )

    # Sign Out Button
    if st.button("🚪 Sign Out", use_container_width=True, key="btn_sign_out"):
        st.session_state.authenticated_user = None
        st.session_state.uploaded_docs = {}
        st.session_state.chat_history = []
        st.session_state.active_page = "Dashboard"
        st.rerun()


# -----------------------------------------------------------------------------
# Main View Router
# -----------------------------------------------------------------------------
if st.session_state.active_page == "Dashboard":
    render_dashboard(
        vector_store=vector_store,
        doc_library=st.session_state.uploaded_docs,
    )

elif st.session_state.active_page == "Document Library":
    render_document_library(
        vector_store=vector_store,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        doc_library=st.session_state.uploaded_docs,
    )

elif st.session_state.active_page == "AI Chat":
    render_chat_interface(
        rag_pipeline=rag_pipeline,
        doc_library=st.session_state.uploaded_docs,
    )

elif st.session_state.active_page == "Document Analysis":
    render_document_analysis(
        summarization_service=summarization_service,
        keypoint_service=keypoint_service,
        doc_library=st.session_state.uploaded_docs,
        vector_store=vector_store,
    )

elif st.session_state.active_page == "Document Comparison":
    render_document_comparison(
        comparison_service=comparison_service,
        doc_library=st.session_state.uploaded_docs,
    )
