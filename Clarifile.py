import streamlit as st
import PyPDF2
import pandas as pd
import docx
import re
from collections import Counter

# -------------------------------
# Test message to confirm deployment
# -------------------------------
st.title("Clarifile App")
st.write("App is running successfully!")

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Clarifile",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Clarifile — Intelligent File Analyzer")
st.write("Upload a document to get summaries, key points, keywords, and answers.")

# -------------------------------
# File Reading Functions
# -------------------------------
def read_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def read_txt(file):
    return file.read().decode("utf-8")

def read_csv(file):
    df = pd.read_csv(file)
    return df.to_string(index=False)

def read_excel(file):
    df = pd.read_excel(file)
    return df.to_string(index=False)

# -------------------------------
# Text Processing Functions
# -------------------------------
def summarize_text(text, max_sentences=5):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:max_sentences])

def extract_key_points(text, count=5):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences[:count]

def extract_keywords(text, top_n=10):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    common_words = Counter(words).most_common(top_n)
    return [word for word, _ in common_words]

def answer_question(text, question):
    sentences = re.split(r'(?<=[.!?]) +', text)
    for s in sentences:
        if any(word.lower() in s.lower() for word in question.split()):
            return s
    return "❌ Answer not found in document."

# -------------------------------
# UI - File Upload
# -------------------------------
uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "txt", "docx", "csv", "xlsx"]
)

document_text = ""

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()

    with st.spinner("Reading document..."):
        if file_type == "pdf":
            document_text = read_pdf(uploaded_file)
        elif file_type == "docx":
            document_text = read_docx(uploaded_file)
        elif file_type == "txt":
            document_text = read_txt(uploaded_file)
        elif file_type == "csv":
            document_text = read_csv(uploaded_file)
        elif file_type == "xlsx":
            document_text = read_excel(uploaded_file)

    st.success("Document loaded successfully!")

# -------------------------------
# Analysis Section
# -------------------------------
if document_text:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Summary")
        st.write(summarize_text(document_text))

        st.subheader("⭐ Key Points")
        for point in extract_key_points(document_text):
            st.write("•", point)

    with col2:
        st.subheader("🔑 Keywords")
        keywords = extract_keywords(document_text)
        st.write(", ".join(keywords))

    st.divider()

    # -------------------------------
    # Q&A Section
    # -------------------------------
    st.subheader("❓ Ask a Question")
    user_question = st.text_input("Type your question")

    if user_question:
        answer = answer_question(document_text, user_question)
        st.info(answer)

    # -------------------------------
    # Full Text (Optional)
    # -------------------------------
    with st.expander("📄 View Full Extracted Text"):
        st.text(document_text)
