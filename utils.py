# utils.py (UPDATED)
import PyPDF2
import streamlit as st
from docx import Document
import re
import json

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF file: {e}.  Please ensure the file is a valid PDF.")
        return None  # Return None to indicate failure
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None # Return None to indicate failure

def extract_text_from_docx(docx_file):
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = Document(docx_file)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return None

def extract_text(uploaded_file): # Renamed function
    """Extracts text from either a PDF or DOCX file."""
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == "application/pdf":
            return extract_text_from_pdf(uploaded_file)  # Correct calls
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(uploaded_file) # Correct calls
        else:
            st.error("Unsupported file type. Please upload a PDF or DOCX file.")
            return None
    else:
        return None

def clean_and_parse_json(response_text):
    """Cleans the response text and parses it as JSON (with error handling)."""
    cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
    start_idx = cleaned_text.find('{')
    end_idx = cleaned_text.rfind('}') + 1

    if start_idx != -1 and end_idx > 0:
        json_str = cleaned_text[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {e}")
            st.code(json_str)  # Display the problematic JSON
            return None  # Return None if parsing fails
    else:
        st.error("No valid JSON found in response.")
        return None
def preprocess_text(text, nlp_model):
    if not nlp_model: return []
    doc = nlp_model(text)
    return [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space and not token.is_stop]
def get_synonyms(word, nlp_model):
    if not nlp_model: return []
    word_doc = nlp_model(word)
    if not word_doc.has_vector:
        return []
    synonyms = [token.text for token in word_doc.vocab if token.has_vector and token.is_lower and token.is_alpha and word_doc.similarity(token) > 0.5 and token.text != word.lower()]
    return list(set(synonyms))