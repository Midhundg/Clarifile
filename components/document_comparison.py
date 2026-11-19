"""Document Comparison component for contrastive multi-document analysis."""

import streamlit as st
from services.comparison_service import ComparisonService


def render_document_comparison(comparison_service: ComparisonService, doc_library: dict):
    """Render a clean, simple, side-by-side document comparison tool."""
    st.markdown("## ⚖️ Compare Documents")
    st.markdown("Select two documents to compare their similarities, differences, and unique content.")

    if len(doc_library) < 2:
        st.warning("Please upload at least two documents in the **Document Library** to compare them.")
        return

    doc_options = {d.file_name: d_id for d_id, d in doc_library.items()}
    names = list(doc_options.keys())

    c1, c2 = st.columns(2)
    with c1:
        doc_a_name = st.selectbox("First Document:", options=names, index=0)
    with c2:
        default_b_idx = 1 if len(names) > 1 else 0
        doc_b_name = st.selectbox("Second Document:", options=names, index=default_b_idx)

    if doc_a_name == doc_b_name:
        st.warning("Please choose two different documents to compare.")
        return

    doc_a = doc_library[doc_options[doc_a_name]]
    doc_b = doc_library[doc_options[doc_b_name]]

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.button("Compare Documents with AI", type="primary"):
        with st.spinner("Comparing document themes and contents..."):
            result = comparison_service.compare_documents(
                doc_a_name=doc_a.file_name,
                doc_a_text=doc_a.full_text,
                doc_b_name=doc_b.file_name,
                doc_b_text=doc_b.full_text,
            )
            st.session_state["last_comparison"] = result

    comp_result = st.session_state.get("last_comparison")

    if comp_result:
        st.markdown("---")
        st.markdown("### Comparison Report")
        st.markdown(comp_result.get("analysis", "No analysis generated."))

        st.markdown("---")
        st.markdown("### Keyword Overlap")
        kw1, kw2, kw3 = st.columns(3)
        with kw1:
            st.markdown(f"**Unique to {doc_a.file_name}:**")
            unique_a = comp_result.get("unique_to_a", [])
            st.markdown(", ".join(unique_a) if unique_a else "None")
        with kw2:
            st.markdown("**Shared Topics:**")
            common = comp_result.get("common_keywords", [])
            st.markdown(", ".join(common) if common else "None")
        with kw3:
            st.markdown(f"**Unique to {doc_b.file_name}:**")
            unique_b = comp_result.get("unique_to_b", [])
            st.markdown(", ".join(unique_b) if unique_b else "None")
