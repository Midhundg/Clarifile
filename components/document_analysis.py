"""Document Analysis component for Summarization, Key Points, and Keywords."""

import streamlit as st
from services.summarization_service import SummarizationService
from services.keypoint_service import KeyPointService
from services.keyword_service import KeywordService


def render_document_analysis(
    summarization_service: SummarizationService,
    keypoint_service: KeyPointService,
    doc_library: dict,
    vector_store,
):
    """Render a clean, simple, and easy-to-use Document Analysis view."""
    st.markdown("## 📊 Document Analysis & Summaries")
    st.markdown("Generate AI summaries, extract key takeaways, and view frequent topics from your files.")

    if not doc_library:
        st.warning("Please upload a document before running analysis.")
        return

    # Select document
    doc_names = [d.file_name for d in doc_library.values()]
    selected_name = st.selectbox("Choose a document to analyze:", options=doc_names)
    doc = next(d for d in doc_library.values() if d.file_name == selected_name)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    tab_summary, tab_keywords = st.tabs(["📝 AI Summary & Key Points", "🔑 Important Keywords"])

    # Tab 1: Summary
    with tab_summary:
        if st.button("✨ Generate AI Summary", type="primary", key="btn_gen_summary"):
            with st.spinner("Analyzing document content..."):
                summaries = summarization_service.summarize_document(
                    full_text=doc.full_text,
                    file_name=doc.file_name,
                )
                st.session_state[f"summary_{doc.doc_id}"] = summaries

        summaries = st.session_state.get(f"summary_{doc.doc_id}")

        if summaries:
            st.markdown("### Executive Summary")
            st.info(summaries["short"])

            st.markdown("### Detailed Breakdown")
            st.markdown(summaries["detailed"])

            st.markdown("### Key Observations")
            st.markdown(summaries["observations"])
        else:
            st.caption("Click **Generate AI Summary** above to read this document's key takeaways.")

    # Tab 2: Keywords
    with tab_keywords:
        st.markdown(f"### Frequent Topics in `{doc.file_name}`")
        keywords = KeywordService.extract_keywords(doc.full_text, top_n=15)

        if keywords:
            chips = " • ".join([f"**{k['keyword']}** ({k['frequency']}x)" for k in keywords])
            st.markdown(chips)
        else:
            st.caption("No significant keywords found.")
