import streamlit as st
import PyPDF2
import pandas as pd
import docx
import re
from collections import Counter

# -------------------------------
# Page Config
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

# -------------------------------
# Improved Question Answering
# -------------------------------
STOP_WORDS = {
    "what", "is", "the", "in", "of", "a", "an", "to", "for",
    "and", "with", "on", "at", "by", "from", "this", "that"
}

def answer_question(text, question):
    q = question.lower()

    # ---------- NAME ----------
    if "name" in q:
        for line in text.splitlines():
            line = line.strip()
            if line.isupper() and 3 < len(line) < 50:
                return line

    # ---------- EMAIL ----------
    if "email" in q:
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if match:
            return match.group()

    # ---------- PHONE ----------
    if "phone" in q or "contact" in q or "mobile" in q:
        match = re.search(r'\b\d{10}\b', text)
        if match:
            return match.group()

    # ---------- LOCATION ----------
    if "location" in q or "city" in q or "place" in q:
        for line in text.splitlines():
            if "coimbatore" in line.lower():
                return line.strip()

    # ---------- CERTIFICATIONS ----------
    if "certification" in q or "certificate" in q:
        lines = text.splitlines()
        capture = False
        certs = []
        for line in lines:
            if "certification" in line.lower():
                capture = True
                continue
            if capture:
                if line.strip() == "":
                    break
                certs.append(line.strip())
        if certs:
            return ", ".join(certs)

    # ---------- FALLBACK: keyword-based ----------
    STOP_WORDS = {
        "what", "is", "the", "in", "of", "a", "an", "to", "for",
        "and", "with", "on", "at", "by", "from"
    }

    sentences = re.split(r'(?<=[.!?]) +', text)
    question_words = [
        w.lower()
        for w in re.findall(r'\b[a-zA-Z]{3,}\b', question)
        if w.lower() not in STOP_WORDS
    ]

    best_sentence = ""
    max_matches = 0

    for s in sentences:
        matches = sum(word in s.lower() for word in question_words)
        if matches > max_matches:
            max_matches = matches
            best_sentence = s

    if best_sentence:
        return best_sentence

    return "❌ Answer not found in document."
