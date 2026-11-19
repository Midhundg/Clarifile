"""AI Chat interface providing grounded RAG question answering with verified citations."""

import streamlit as st
from services.rag_pipeline import RAGPipeline
from utils.config import Config


def render_chat_interface(rag_pipeline: RAGPipeline, doc_library: dict):
    """Render a clean, intuitive AI Chat interface with proper outlines and attractive accents."""
    st.markdown("## 💬 AI Document Chat")
    st.caption("Ask any question. Clarifile searches your uploaded files and gives accurate answers with sources.")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    if not doc_library:
        st.warning("Please upload at least one document before chatting.")
        if st.button("Upload Documents", type="primary"):
            st.session_state.active_page = "Document Library"
            st.rerun()
        return

    # Check for targeted document pre-selection from Dashboard
    target_doc_id = st.session_state.pop("target_chat_doc", None)

    # Top Control Bar Inside a Crisp Box
    with st.container(border=True):
        col_scope, col_clear = st.columns([5, 1], vertical_alignment="center")

        with col_scope:
            doc_options = {"🌐 All Documents (Global Search)": None}
            default_index = 0
            idx_counter = 1
            for d_id, d in doc_library.items():
                label = f"📄 {d.file_name} ({d.file_type.upper()})"
                doc_options[label] = d_id
                if target_doc_id and d_id == target_doc_id:
                    default_index = idx_counter
                idx_counter += 1

            selected_label = st.selectbox(
                "Search in",
                options=list(doc_options.keys()),
                index=default_index,
                label_visibility="collapsed",
            )
            selected_doc_id = doc_options[selected_label]

        with col_clear:
            if st.session_state.get("chat_history"):
                if st.button("🧹 Clear", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Helpful Starter Question Pills (Inside a neat container when chat is empty)
    if not st.session_state.chat_history:
        is_dark = st.session_state.get("ui_theme") == "Dark"
        sq_color = "#93C5FD" if is_dark else "#1E40AF"
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-weight: 600; font-size: 0.95rem; color: {sq_color}; margin-bottom: 8px;">
                    ✨ Suggested Questions
                </div>
                """,
                unsafe_allow_html=True,
            )
            p_col1, p_col2, p_col3 = st.columns(3)
            sample_questions = [
                "What are the main tools and technologies mentioned?",
                "Can you give me a summary of key points?",
                "What are the core technical decisions and skills?",
            ]
            for i, q in enumerate(sample_questions):
                with [p_col1, p_col2, p_col3][i]:
                    if st.button(f"👉 {q}", key=f"sq_{i}", use_container_width=True):
                        st.session_state.pending_query = q
                        st.rerun()

    # Render Conversation Messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Clean, quiet source box
            if msg.get("sources"):
                with st.expander(f"📚 {len(msg['sources'])} Cited Source Passages", expanded=False):
                    for i, source in enumerate(msg["sources"], start=1):
                        page_label = f"Page {source.page_number}" if str(source.page_number).isdigit() else f"Section: {source.page_number}"
                        st.markdown(f"**Source {i}:** `{source.file_name}` — {page_label} *(Relevance: {source.score:.0%})*")
                        st.caption(f'"{source.text}"')

    # Chat Input
    pending = st.session_state.pop("pending_query", None)
    user_query = st.chat_input("Ask a question about your documents...")

    active_query = pending or user_query

    if active_query:
        st.session_state.chat_history.append({"role": "user", "content": active_query})

        with st.chat_message("user"):
            st.markdown(active_query)

        with st.chat_message("assistant"):
            with st.spinner("Finding relevant passages & generating answer..."):
                rag_response = rag_pipeline.answer_question(
                    question=active_query,
                    doc_id=selected_doc_id,
                    top_k=Config.DEFAULT_TOP_K,
                    similarity_threshold=Config.SIMILARITY_THRESHOLD,
                )
                st.markdown(rag_response.answer)

                if rag_response.sources:
                    with st.expander(f"📚 {len(rag_response.sources)} Cited Source Passages", expanded=False):
                        for i, source in enumerate(rag_response.sources, start=1):
                            page_label = f"Page {source.page_number}" if str(source.page_number).isdigit() else f"Section: {source.page_number}"
                            st.markdown(f"**Source {i}:** `{source.file_name}` — {page_label} *(Relevance: {source.score:.0%})*")
                            st.caption(f'"{source.text}"')

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": rag_response.answer,
            "sources": rag_response.sources,
        })
