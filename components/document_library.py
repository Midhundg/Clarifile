"""Document Library component for multi-format upload, ingestion, vectorization, and index management."""

import streamlit as st
from services.document_loader import DocumentLoader
from services.chunking import ChunkingService
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from utils.helpers import format_file_size


def render_document_library(
    vector_store: VectorStore,
    chunking_service: ChunkingService,
    embedding_service: EmbeddingService,
    doc_library: dict,
):
    """Render a clean Document Library with proper outlines and attractive accents."""
    is_dark = st.session_state.get("ui_theme") == "Dark"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#64748B"
    divider_color = "#334155" if is_dark else "#CBD5E1"
    upload_title_color = "#86EFAC" if is_dark else "#166534"

    st.markdown("## 📚 Document Library")
    st.caption("Upload documents to your knowledge base. Files are automatically extracted, chunked, and indexed.")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Session alert tracking
    if "lib_alert" not in st.session_state:
        st.session_state.lib_alert = None

    if st.session_state.lib_alert:
        alert = st.session_state.lib_alert
        if alert["type"] == "success":
            st.success(alert["msg"])
        elif alert["type"] == "error":
            st.error(alert["msg"])
        st.session_state.lib_alert = None

    # Upload Box with Proper Outline and Soft Emerald Theme
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 22px;">📤</span>
                <span style="font-weight: 700; font-size: 1.1rem; color: {upload_title_color};">Upload New Documents</span>
            </div>
            <div style="font-size: 0.88rem; color: {text_secondary}; margin-bottom: 12px;">
                Drop PDF, Word (DOCX), Apple Pages (.pages), Excel (XLSX), CSV, or plain text files.
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "docx", "txt", "csv", "xlsx", "pages"],
            accept_multiple_files=True,
            help="Supported formats: PDF, Word (DOCX), Apple Pages, Excel, CSV, Text.",
            label_visibility="collapsed",
        )

        if uploaded_files:
            new_files = [f for f in uploaded_files if not any(d.file_name == f.name for d in doc_library.values())]

            if new_files:
                with st.spinner(f"Indexing {len(new_files)} new document(s)..."):
                    for file_obj in new_files:
                        try:
                            extracted_doc = DocumentLoader.load_document(
                                file_source=file_obj,
                                file_name=file_obj.name,
                                file_size=file_obj.size,
                            )
                            chunks = chunking_service.chunk_document(extracted_doc)
                            chunk_texts = [c.text for c in chunks]
                            embeddings = embedding_service.embed_texts(chunk_texts)
                            vector_store.add_chunks(chunks, embeddings)
                            doc_library[extracted_doc.doc_id] = extracted_doc

                            st.session_state.lib_alert = {
                                "type": "success",
                                "msg": f"✅ Indexed **{extracted_doc.file_name}** ({extracted_doc.num_pages} pages, {len(chunks)} chunks).",
                            }
                        except Exception as e:
                            st.session_state.lib_alert = {
                                "type": "error",
                                "msg": f"❌ Could not process '{file_obj.name}': {str(e)}",
                            }

                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Document List Header
    col_hdr, col_reset = st.columns([5, 2], vertical_alignment="center")
    with col_hdr:
        st.markdown(f"### Uploaded Documents ({len(doc_library)})")
    with col_reset:
        if doc_library:
            if st.button("Clear All Files", type="secondary", use_container_width=True):
                vector_store.clear_all()
                doc_library.clear()
                st.session_state.chat_history = []
                st.rerun()

    if not doc_library:
        st.info("No documents uploaded yet. Drop a file in the box above to get started.")
        return

    for doc_id, doc in list(doc_library.items()):
        if is_dark:
            if doc.file_type.lower() == "pdf":
                badge_color = "#FCA5A5"
                badge_bg = "rgba(239, 68, 68, 0.2)"
                badge_border = "rgba(239, 68, 68, 0.4)"
            elif doc.file_type.lower() == "pages":
                badge_color = "#D8B4FE"
                badge_bg = "rgba(168, 85, 247, 0.2)"
                badge_border = "rgba(168, 85, 247, 0.4)"
            elif doc.file_type.lower() in ["xlsx", "csv"]:
                badge_color = "#6EE7B7"
                badge_bg = "rgba(16, 185, 129, 0.2)"
                badge_border = "rgba(16, 185, 129, 0.4)"
            else:
                badge_color = "#93C5FD"
                badge_bg = "rgba(59, 130, 246, 0.2)"
                badge_border = "rgba(59, 130, 246, 0.4)"
        else:
            if doc.file_type.lower() == "pdf":
                badge_color = "#DC2626"
                badge_bg = "#FEF2F2"
                badge_border = "#FECACA"
            elif doc.file_type.lower() == "pages":
                badge_color = "#7C3AED"
                badge_bg = "#F5F3FF"
                badge_border = "#DDD6FE"
            elif doc.file_type.lower() in ["xlsx", "csv"]:
                badge_color = "#059669"
                badge_bg = "#ECFDF5"
                badge_border = "#A7F3D0"
            else:
                badge_color = "#2563EB"
                badge_bg = "#EFF6FF"
                badge_border = "#BFDBFE"

        with st.container(border=True):
            c_icon, c_info, c_sep, c_details, c_chat, c_del = st.columns(
                [0.5, 4.3, 0.2, 3.0, 1.1, 0.9],
                vertical_alignment="center",
            )

            with c_icon:
                st.markdown("<div style='font-size: 26px; text-align: center;'>📄</div>", unsafe_allow_html=True)

            with c_info:
                st.markdown(
                    f"""
                    <div style="line-height: 1.25;">
                        <div style="font-weight: 700; font-size: 0.98rem; color: {text_primary}; margin-bottom: 3px;">
                            {doc.file_name}
                        </div>
                        <div style="font-size: 0.78rem; color: {text_secondary};">
                            <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border}; padding: 1px 7px; border-radius: 4px; font-weight: 600; font-size: 0.72rem; text-transform: uppercase;">{doc.file_type}</span>
                            <span style="margin-left: 6px; color: {text_secondary};">Document</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_sep:
                st.markdown(
                    f"<div style='border-left: 1.5px solid {divider_color}; height: 38px; margin: 0 auto;'></div>",
                    unsafe_allow_html=True,
                )

            with c_details:
                st.markdown(
                    f"""
                    <div style="line-height: 1.25; padding-left: 4px;">
                        <div style="font-weight: 600; font-size: 0.92rem; color: {text_primary}; margin-bottom: 2px;">
                            📄 {doc.num_pages} page(s) &nbsp;•&nbsp; 📝 {doc.total_words:,} words
                        </div>
                        <div style="font-size: 0.78rem; color: {text_secondary};">
                            Size: {format_file_size(doc.file_size)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_chat:
                if st.button("💬 Chat", key=f"lib_chat_{doc_id}", use_container_width=True):
                    st.session_state.active_page = "AI Chat"
                    st.session_state.target_chat_doc = doc_id
                    st.rerun()

            with c_del:
                if st.button("Delete", key=f"lib_del_{doc_id}", use_container_width=True):
                    vector_store.delete_document(doc_id)
                    del doc_library[doc_id]
                    st.rerun()

            with st.expander(f"Preview text of {doc.file_name}", expanded=False):
                st.text_area("Extracted Text", doc.full_text, height=200, disabled=True, key=f"pv_{doc_id}")
