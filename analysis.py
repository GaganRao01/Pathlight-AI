# analysis.py (COMPREHENSIVELY CORRECTED)

import json
import streamlit as st
import re
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
import faiss
import torch
from utils import clean_and_parse_json

# Load Models (Cached)
@st.cache_resource
def get_spacy_model():
    try:
        nlp = spacy.load("en_core_web_sm")
        return nlp
    except OSError:
        st.error("Could not load 'en_core_web_sm'. Run: python -m spacy download en_core_web_sm")
        return None

@st.cache_resource
def get_hf_model_and_tokenizer(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    try:
        model = SentenceTransformer(model_name)
        return model, model.tokenizer
    except Exception as e:
        st.error(f"Could not load Hugging Face model: {e}")
        return None, None

# --- Preprocessing ---
def preprocess_text(text, nlp_model):
    if not nlp_model: return []
    doc = nlp_model(text)
    return [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space and not token.is_stop]

# --- Synonyms ---
def get_synonyms(word, nlp_model):
    if not nlp_model: return []
    word_doc = nlp_model(word)
    if not word_doc.has_vector:
        return []
    synonyms = [token.text for token in word_doc.vocab if token.has_vector and token.is_lower and token.is_alpha and word_doc.similarity(token) > 0.5 and token.text != word.lower()]
    return list(set(synonyms))

# --- Keyword Matching ---
def refined_keyword_match_score(job_description, resume_text, nlp_model):
    if not nlp_model: return 0.0
    job_keywords = preprocess_text(job_description, nlp_model)
    resume_keywords = preprocess_text(resume_text, nlp_model)
    expanded_job_keywords = set(job_keywords)
    for keyword in job_keywords:
        expanded_job_keywords.update(get_synonyms(keyword, nlp_model))
    if not expanded_job_keywords: return 0.0
    match_count = sum(1 for keyword in resume_keywords if keyword in expanded_job_keywords)
    return (match_count / len(expanded_job_keywords)) * 100 if expanded_job_keywords else 0.0

# --- Embedding Generation ---
def generate_embedding_hf(text, model, tokenizer):
    if not model or not tokenizer: return None
    try:
        embeddings = model.encode(text, convert_to_tensor=True)
        return embeddings.cpu().numpy()  # Move to CPU and convert to NumPy
    except Exception as e:
        st.error(f"Error in generate_embedding_hf: {e}")
        return None

# --- FAISS Indexing ---
def create_faiss_index(embeddings):
    """Creates a FAISS index, handling single and multiple embeddings."""
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)  # Ensure 2D
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype(np.float32)) # Ensure float32 for FAISS
    return index

def query_faiss(index, query_embedding, k=1):
    """Queries FAISS, handling single embeddings."""
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    distances, indices = index.search(query_embedding.astype(np.float32), k)
    return distances, indices

# --- Hybrid Score Calculation ---
def calculate_hybrid_score(job_description, resume_text, model, tokenizer, nlp_model, alpha=0.6):
    """Calculates hybrid score: keyword match and semantic similarity."""
    if not nlp_model or not model or not tokenizer:
        return 0.0, 0.0

    keyword_score = refined_keyword_match_score(job_description, resume_text, nlp_model)

    # Handle empty job description or resume text explicitly
    if not job_description:
        job_embedding = np.zeros((1, model.get_sentence_embedding_dimension()), dtype=np.float32) # Create a zero vector
    else:
        job_embedding = generate_embedding_hf(job_description, model, tokenizer)
        if job_embedding is None:
            return keyword_score, 0.0
        job_embedding = job_embedding.astype(np.float32)


    if not resume_text:
          resume_embedding = np.zeros((1, model.get_sentence_embedding_dimension()), dtype=np.float32)
    else:
        resume_embedding = generate_embedding_hf(resume_text, model, tokenizer)
        if resume_embedding is None:
            return keyword_score, 0.0
        resume_embedding = resume_embedding.astype(np.float32)

    # Ensure 2D arrays
    if job_embedding.ndim == 1:
        job_embedding = job_embedding.reshape(1, -1)
    if resume_embedding.ndim == 1:
        resume_embedding = resume_embedding.reshape(1, -1)


    index = create_faiss_index(resume_embedding)
    distances, _ = query_faiss(index, job_embedding)

    # --- Corrected Similarity Score Calculation ---
    if distances.size > 0:
        #  Normalize the distance. The maximum possible distance is sqrt(2)
        #  because the embeddings are L2 normalized by SentenceTransformers.
        normalized_distance = distances[0][0] / np.sqrt(2)
        similarity_score = max(0.0, min(100.0, 100 * (1 - normalized_distance)))
    else:
        similarity_score = 0.0

    hybrid_score = alpha * keyword_score + (1 - alpha) * similarity_score
    return hybrid_score, similarity_score


def get_match_analysis(model, job_description, resume_text):
    nlp_model = get_spacy_model()
    hf_model, tokenizer = get_hf_model_and_tokenizer()

    if nlp_model is None or hf_model is None or tokenizer is None:
      st.error("Model loading failed. Cannot perform analysis.")
      return None
    hybrid_score, semantic_similarity_score = calculate_hybrid_score(job_description, resume_text, hf_model, tokenizer, nlp_model)
    keyword_score = refined_keyword_match_score(job_description, resume_text, nlp_model)

    prompt = f"""
    Act as an expert ATS (Applicant Tracking System) scanner and professional resume analyst. Analyze the provided job description and resume.

    Provide a detailed analysis in JSON format, explaining *why* certain skills or experiences are considered missing or weak, and offer specific, actionable recommendations. Include links to relevant resources (courses, certification programs, articles) where appropriate.
    The hybrid match score between the resume and job description is {hybrid_score:.2f} (Keyword Match: {keyword_score:.2f}, Semantic Similarity: {semantic_similarity_score:.2f}). Consider this score when assessing the overall match and providing recommendations.  A higher score indicates a better match.

    Return ONLY the following JSON format with no additional text, comments, or markdown formatting:

    {{
        "overall_match": <number between 0-100>,
        "keyword_match_score": <number between 0-100>,
        "keywords_from_job_description": ["<keyword 1>", "<keyword 2>", ...],
        "categories": {{
            "technical_skills": {{
                "match": <number between 0-100>,
                "present_skills": [<list of matching technical skills found>],
                "missing_skills": [{{
                    "skill": "<missing skill name>",
                    "reason": "<explanation of why it's missing/important>",
                    "remediation_suggestions": ["<actionable suggestion 1>", "<actionable suggestion 2>"],
                    "resource_links": [
                        {{"title": "<resource title>", "url": "<resource URL>"}},
                        {{"title": "<resource title>", "url": "<resource URL>"}}
                    ]
                }}],
                "improvement_suggestions": ["<general suggestion 1>", "<general suggestion 2>"]
            }},
            "soft_skills": {{
                "match": <number between 0-100>,
                "present_skills": [<list of matching soft skills found>],
                "missing_skills": [{{
                    "skill": "<missing skill name>",
                    "reason": "<explanation of why it's missing/important>",
                    "remediation_suggestions": ["<actionable suggestion 1>", "<actionable suggestion 2>"]
                }}],
                "improvement_suggestions": ["<general suggestion 1>", "<general suggestion 2>"]
            }},
            "experience": {{
                "match": <number between 0-100>,
                "strengths": ["<strength 1>", "<strength 2>"],
                "gaps": [{{
                    "gap": "<experience gap>",
                    "reason": "<explanation of the gap>",
                    "remediation_suggestions": ["<actionable suggestion 1>", "<actionable suggestion 2>"]
                }}],
                "improvement_suggestions": ["<general suggestion 1>", "<general suggestion 2>"]
            }},
            "education": {{
                "match": <number between 0-100>,
                "relevant_qualifications": ["<qualification 1>", "<qualification 2>"],
                "gaps": [{{
                    "gap": "<educational gap>",
                    "reason": "<explanation of the gap>",
                    "remediation_suggestions": ["<actionable suggestion 1>", "<actionable suggestion 2>"],
                    "resource_links": [
                        {{"title": "<resource title>", "url": "<resource URL>"}}
                    ]

                }}],
                "improvement_suggestions": ["<general suggestion 1>", "<general suggestion 2>"]
            }}
        }},
        "ats_optimization": {{
            "formatting_issues": ["<issue 1>", "<issue 2>"],
            "keyword_optimization": ["<suggestion 1>", "<suggestion 2>"],
            "section_improvements": ["<suggestion 1>", "<suggestion 2>"]
        }},
        "impact_scoring": {{
            "achievement_metrics": <number between 0-100>,
            "action_verbs": <number between 0-100>,
            "quantifiable_results": <number between 0-100>,
            "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"]
        }}
    }}

    Job Description: {job_description}

    Resume: {resume_text}
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        response_text = response_text.replace('\n', ' ').replace('\r', '')
        response_text = ' '.join(response_text.split())

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx != -1 and end_idx != 0:
            json_str = response_text[start_idx:end_idx]
            analysis = json.loads(json_str)
             # Assign the calculated scores
            analysis['overall_match'] = round(hybrid_score)  # Use hybrid score
            analysis['keyword_match_score'] = round(keyword_score)  # Include keyword score
            analysis['semantic_similarity_score'] = round(semantic_similarity_score)
            return analysis
        else:
            raise ValueError("Could not find valid JSON in the response")


    except Exception as e:
      # Fallback (Simplified Prompt)
      try:
            simplified_prompt = f"""
            Analyze the job description and resume below. Return ONLY a JSON object in this exact format:
            The hybrid match score between the resume and job description is {hybrid_score:.2f} (Keyword Match: {keyword_score:.2f}, Semantic Similarity: {semantic_similarity_score:.2f}).
            {{
                "overall_match": <number>,
                "keyword_match_score": <number>,
                "keywords_from_job_description": ["<keyword 1>", "<keyword 2>", ...],
                "categories": {{
                    "technical_skills": {{"match": <number>, "present_skills": [], "missing_skills": [], "improvement_suggestions": []}},
                    "soft_skills": {{"match": <number>, "present_skills": [], "missing_skills": [], "improvement_suggestions": []}},
                    "experience": {{"match": <number>, "strengths": [], "gaps": [], "improvement_suggestions": []}},
                    "education": {{"match": <number>, "relevant_qualifications": [], "improvement_suggestions": []}}
                }},
                "ats_optimization": {{"formatting_issues": [], "keyword_optimization": [], "section_improvements": []}},
                "impact_scoring": {{"achievement_metrics": <number>, "action_verbs": <number>, "quantifiable_results": <number>, "improvement_suggestions": []}}
            }}

            Job Description: {job_description}
            Resume: {resume_text}
            """

            retry_response = model.generate_content(simplified_prompt)
            retry_text = retry_response.text.strip()
            retry_text = retry_text.replace('```json', '').replace('```', '').strip()

            start_idx = retry_text.find('{')
            end_idx = retry_text.rfind('}') + 1
            json_str = retry_text[start_idx:end_idx]
            analysis = json.loads(json_str)
            analysis['overall_match'] = round(hybrid_score)  # Use hybrid score
            analysis['keyword_match_score'] = round(keyword_score)
            analysis['semantic_similarity_score'] = round(semantic_similarity_score)
            return analysis


      except Exception as retry_error:
            st.error(f"Retry failed: {str(retry_error)}")
            raise

def get_resume_enhancement_suggestions(model, resume_text, match_analysis=None):
    """Get resume enhancement suggestions (independent of job description)."""

    nlp_model = get_spacy_model()
    hf_model, tokenizer = get_hf_model_and_tokenizer()


    if match_analysis:
        hybrid_score = match_analysis.get('overall_match', 0.0)
        keyword_score = match_analysis.get('keyword_match_score',0.0)
        semantic_similarity_score = 0.0
        if hf_model and tokenizer:
            _, semantic_similarity_score = calculate_hybrid_score("", resume_text,  hf_model, tokenizer, nlp_model) #job description is empty here

    else:
        hybrid_score = 0.0
        keyword_score = 0.0
        semantic_similarity_score = 0.0
        if hf_model and tokenizer:
             _, semantic_similarity_score = calculate_hybrid_score("", resume_text, hf_model, tokenizer, nlp_model) #job_descrition is empty here
    # Build the prompt conditionally based on whether match_analysis is provided
    prompt = f"""
    Analyze this resume and provide *highly specific* and *personalized* enhancement suggestions.
    Focus on improving clarity, impact, keyword optimization, and overall effectiveness
    for modern Applicant Tracking Systems (ATS) and recruiters.  Provide concrete examples
    and alternative wording.  Be extremely detailed.
    The hybrid match score for this resume (or in comparison to a generic job description) is {hybrid_score:.2f} (Keyword Match {keyword_score:.2f}, Semantic Similarity: {semantic_similarity_score:.2f}). Consider this score when making suggestions.

    """

    if match_analysis:  # If match analysis is provided, include missing skills
        missing_skills_prompt = ""
        if 'categories' in match_analysis and 'technical_skills' in match_analysis['categories'] and 'missing_skills' in match_analysis['categories']['technical_skills']:
            missing_skills = match_analysis['categories']['technical_skills']['missing_skills']
            if missing_skills:
                missing_skills_prompt += "The following technical skills are MISSING from the resume, based on a comparison with a relevant job description:\n"
                for skill_info in missing_skills:
                    missing_skills_prompt += f"- {skill_info['skill']}: {skill_info['reason']}\n"
                missing_skills_prompt += "Consider these missing skills when suggesting certifications and technologies.\n"
        if 'categories' in match_analysis and 'soft_skills' in match_analysis['categories'] and 'missing_skills' in match_analysis['categories']['soft_skills']:
            missing_skills = match_analysis['categories']['soft_skills']['missing_skills']
            if missing_skills:
                missing_skills_prompt += "The following soft skills are MISSING from the resume, based on a comparison with a relevant job description:\n"
                for skill_info in missing_skills:
                    missing_skills_prompt += f"- {skill_info['skill']}: {skill_info['reason']}\n"
                missing_skills_prompt += "Consider these missing skills when suggesting improvements.\n"

        prompt += missing_skills_prompt

    prompt += f"""
    Return ONLY a JSON object in this exact format (no surrounding text or markdown):

    {{
        "summary_section": {{
            "has_summary": <true or false>,
            "suggestions": ["<Be specific.  Rewrite sentences.  Explain *why* a change is needed.>", ...],
            "sample_summary": "<A complete, rewritten example summary based on the resume, incorporating best practices.>"
        }},
        "bullet_points": {{
            "strength": <number between 0-100 representing overall strength>,
            "weak_bullets": [
                {{"original": "<original bullet point text>", "improved": "<rewritten, improved bullet point>", "reason": "<why was it weak and how is it improved?>"}},
                ...
            ],
            "general_suggestions": ["<Address issues common across multiple bullets.>", "<Focus on quantifiable results.>", ...]
        }},
        "power_verbs": {{
            "current_verbs": ["<verb 1>", "<verb 2>", ...],
            "suggested_verbs": ["<stronger verb 1>", "<stronger verb 2>", ...],
            "explanation": "<Explain why the suggested verbs are better, e.g., more active, more specific.>"
        }},
        "keywords": {{
            "present_keywords": ["<keyword 1>", "<keyword 2>", ...],
            "missing_keywords": ["<keyword 1>", "<keyword 2>", ...],
            "suggestions": ["<Explain how to incorporate missing keywords naturally.>", "<Suggest specific phrases.>", ...]
        }},
        "technical_profile": {{
            "technologies_to_add": ["<Suggest specific technologies based on industry trends, the user's likely career path, AND any missing skills identified in the job description analysis.>", ...],
            "certifications": [
                {{"certification_name": "<Name of Certification>", "url": "<Link to certification information>", "relevance": "<Why this certification is relevant to the resume AND addresses missing skills/career goals.>"}},
                ...
            ]
        }},
         "soft_skills": {{
            "soft_skills_to_add": ["<Suggest specific soft skills based on industry trends,the user's likely career path, AND any missing skills identified in the job description analysis.>", ...],
            "soft_skills_improvement_suggestions": ["<Suggest how to incorporate or improve the soft on the resume>",
            "..."]
        }},
        "overall_suggestions": [
            "<Address any major structural issues.>",
            "<Suggest changes to section order, if needed.>",
            "<Comment on overall tone and style.>",
            "<Point out any inconsistencies or redundancies.>",
            "<Suggest specific formatting improvements (e.g., consistent use of bolding).>"
        ]
    }}

    Resume text:

    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        return clean_and_parse_json(response.text)
    except Exception as e:
        st.error(f"Error generating resume enhancement suggestions: {str(e)}")
        return None

def get_job_description_keywords(job_description):
    """Extracts keywords from a job description using the Gemini model, and preprocess."""
    nlp_model = get_spacy_model()
    prompt = f"""
    You are an expert job description analyzer. Extract the key skills, technologies,
    and qualifications from the following job description.  Return ONLY a JSON array
    of strings, with NO other text or formatting.

    ["<keyword 1>", "<keyword 2>", "<keyword 3>", ...]

    Job Description:
    ```
    {job_description}
    ```
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        # Use regex to handle cases where the response might not be *perfectly* clean JSON.
        match = re.search(r'\[.*?\]', response.text, re.DOTALL)
        if match:
            json_str = match.group(0)
            keywords =  json.loads(json_str)
            # Apply preprocessing to the keywords
            processed_keywords = []
            for keyword in keywords:
                processed_keywords.extend(preprocess_text(keyword, nlp_model))

            return list(set(processed_keywords)) # Remove duplicates

        else:
            st.error("Could not extract keywords from job description.")
            return []
    except Exception as e:
        st.error(f"Error extracting keywords: {e}")
        return []