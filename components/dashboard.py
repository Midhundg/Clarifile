"""Dashboard component displaying operational metrics, recent documents, and quick actions."""

import os
import streamlit as st
from utils.helpers import format_file_size


def render_dashboard(vector_store, doc_library: dict):
    """Render a clean, minimalist dashboard with crisp, colorful, well-outlined action boxes."""
    is_dark = st.session_state.get("ui_theme") == "Dark"

    # Theme-adaptive palette tokens
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#64748B"
    divider_color = "#334155" if is_dark else "#CBD5E1"

    # Quick action colors (high-contrast vibrant colors in dark mode)
    box_blue_title = "#93C5FD" if is_dark else "#1E40AF"
    box_blue_bg = "rgba(59, 130, 246, 0.16)" if is_dark else "#EFF6FF"
    box_blue_border = "#3B82F6" if is_dark else "#93C5FD"

    box_green_title = "#86EFAC" if is_dark else "#166534"
    box_green_bg = "rgba(34, 197, 94, 0.16)" if is_dark else "#F0FDF4"
    box_green_border = "#22C55E" if is_dark else "#86EFAC"

    box_purple_title = "#D8B4FE" if is_dark else "#6B21A8"
    box_purple_bg = "rgba(168, 85, 247, 0.16)" if is_dark else "#FAF5FF"
    box_purple_border = "#A855F7" if is_dark else "#C4B5FD"

    st.markdown("## 📊 Dashboard")
    st.caption("Welcome to Clarifile. Chat with your documents, generate summaries, and compare technical notes.")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    total_docs = len(doc_library)
    total_chunks = vector_store.get_total_chunks()
    total_pages = sum(d.num_pages for d in doc_library.values())

    # 3 Metrics with crisp outlines
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Documents Ingested", f"{total_docs}")
    with c2:
        st.metric("Indexed Pages", f"{total_pages}")
    with c3:
        st.metric("Knowledge Chunks", f"{total_chunks:,}")

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 3 Distinct, Beautifully Outlined Quick Action Boxes (Button INSIDE the box!)
    st.markdown("### Quick Actions")
    act_c1, act_c2, act_c3 = st.columns(3)

    # Box 1: Ask a Question (Contained Box with Blue Accent)
    with act_c1:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align: center; padding: 6px 4px 10px 4px;">
                    <div style="
                        width: 48px; height: 48px; margin: 0 auto 10px auto;
                        background: {box_blue_bg}; border: 1.5px solid {box_blue_border}; border-radius: 12px;
                        display: flex; align-items: center; justify-content: center; font-size: 24px;
                    ">💬</div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: {box_blue_title}; margin-bottom: 4px;">Ask a Question</div>
                    <div style="font-size: 0.85rem; color: {text_secondary}; min-height: 38px; line-height: 1.35;">
                        Chat naturally with verified citations from your documents
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open AI Chat →", key="btn_dash_chat", use_container_width=True, type="primary"):
                st.session_state.active_page = "AI Chat"
                st.rerun()

    # Box 2: Upload Files (Contained Box with Green Accent)
    with act_c2:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align: center; padding: 6px 4px 10px 4px;">
                    <div style="
                        width: 48px; height: 48px; margin: 0 auto 10px auto;
                        background: {box_green_bg}; border: 1.5px solid {box_green_border}; border-radius: 12px;
                        display: flex; align-items: center; justify-content: center; font-size: 24px;
                    ">📤</div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: {box_green_title}; margin-bottom: 4px;">Upload Files</div>
                    <div style="font-size: 0.85rem; color: {text_secondary}; min-height: 38px; line-height: 1.35;">
                        Add PDF, Word, Pages, Excel, CSV, or Text files
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Upload Documents →", key="btn_dash_upload", use_container_width=True):
                st.session_state.active_page = "Document Library"
                st.rerun()

    # Box 3: Summarize & Analyze (Contained Box with Purple Accent)
    with act_c3:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align: center; padding: 6px 4px 10px 4px;">
                    <div style="
                        width: 48px; height: 48px; margin: 0 auto 10px auto;
                        background: {box_purple_bg}; border: 1.5px solid {box_purple_border}; border-radius: 12px;
                        display: flex; align-items: center; justify-content: center; font-size: 24px;
                    ">📝</div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: {box_purple_title}; margin-bottom: 4px;">Summarize & Analyze</div>
                    <div style="font-size: 0.85rem; color: {text_secondary}; min-height: 38px; line-height: 1.35;">
                        Extract executive takeaways, key facts, and keywords
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("View Summaries →", key="btn_dash_analysis", use_container_width=True):
                st.session_state.active_page = "Document Analysis"
                st.rerun()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Document List with Tight Name-Type Grouping & Vertical Separator Line
    st.markdown(f"### Your Documents ({total_docs})")

    if not doc_library:
        st.info("No documents are uploaded yet. Click **Upload Documents** above to add your first file.")
    else:
        for doc in doc_library.values():
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
                col_icon, col_info, col_sep, col_meta, col_btn = st.columns(
                    [0.6, 4.6, 0.2, 3.2, 1.4],
                    vertical_alignment="center",
                )
                with col_icon:
                    st.markdown("<div style='font-size: 26px; text-align: center;'>📄</div>", unsafe_allow_html=True)

                with col_info:
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

                with col_sep:
                    st.markdown(
                        f"<div style='border-left: 1.5px solid {divider_color}; height: 38px; margin: 0 auto;'></div>",
                        unsafe_allow_html=True,
                    )

                with col_meta:
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

                with col_btn:
                    if st.button("💬 Chat", key=f"dash_chat_{doc.doc_id}", use_container_width=True):
                        st.session_state.active_page = "AI Chat"
                        st.session_state.target_chat_doc = doc.doc_id
                        st.rerun()

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Downloadable Documentation Card
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-weight: 700; font-size: 1.05rem; color: {text_primary}; margin-bottom: 3px;">
                        📥 Download System Documentation
                    </div>
                    <div style="font-size: 0.84rem; color: {text_secondary};">
                        Complete architecture, tech stack, data pipelines, RAG workflows, and multi-user security guide.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        c_pdf, c_docx = st.columns(2)
        with c_pdf:
            if os.path.exists("Clarifile_Complete_System_Documentation.pdf"):
                with open("Clarifile_Complete_System_Documentation.pdf", "rb") as f:
                    st.download_button(
                        label="📄 Download Documentation (PDF)",
                        data=f.read(),
                        file_name="Clarifile_Complete_System_Documentation.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_dash_dl_pdf",
                    )
        with c_docx:
            if os.path.exists("Clarifile_Complete_System_Documentation.docx"):
                with open("Clarifile_Complete_System_Documentation.docx", "rb") as f:
                    st.download_button(
                        label="📝 Download Documentation (Word DOCX)",
                        data=f.read(),
                        file_name="Clarifile_Complete_System_Documentation.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="btn_dash_dl_docx",
                    )
