# career_roadmap.py (Revised Prompt for Better URLs)

import google.generativeai as genai
import streamlit as st
import json
import re
from utils import clean_and_parse_json # Use the robust parser

def generate_career_roadmap(model, resume_text):
    """
    Generates a personalized and actionable career roadmap in a structured JSON format,
    suitable for a rich UI display, based on the provided resume.
    Emphasizes finding valid URLs for resources.
    """
    prompt = f"""
Act as an insightful and encouraging Senior Career Strategist. Based *only* on the detailed analysis of the provided RESUME, create a comprehensive, actionable, and personalized career roadmap presented as a structured JSON object.

**CRITICAL INSTRUCTIONS:**

*   **INFER & RECOMMEND:** Analyze skills, experience, projects, education. Infer a logical, ambitious **Next Step Focus Area**. Justify clearly, linking to RESUME evidence.
*   **ACTION-ORIENTED GOALS:** For each timeframe (Short, Mid, Long), provide 3-4 distinct, concrete, actionable goals (skills, projects, certs, networking).
*   **SPECIFICITY:** Avoid vague advice. Be precise (e.g., "Master Pandas/Scikit-learn," not just "Learn Python").
*   **RESOURCES & VALID URLS:** Provide relevant, specific resource names (e.g., "Coursera's Deep Learning Specialization," "AWS Certified Solutions Architect - Associate"). **CRITICAL: Make a strong effort to find and include a valid, specific, publicly accessible URL (https://...) for each resource.** Use "#" or omit the "url" field ONLY as a last resort if a suitable, specific link cannot be found after a reasonable attempt (e.g., for very generic resources like 'Personal Project Repository' or 'Study Group'). Do NOT provide internal/invalid URLs.
*   **SKILLS BREAKDOWN:** Summarize key Technical and Soft/Leadership skills to develop.
*   **STRUCTURED JSON:** Output ONLY a valid JSON object adhering strictly to the format below. Ensure all strings are correctly escaped. No introductory text, comments, or markdown outside the JSON.

**JSON FORMAT:**

```json
{{
  "recommended_focus_area": "<Specific, ambitious next step role/specialization>",
  "justification": "<Concise justification linking recommendation to RESUME evidence (skills, experience, projects).>",
  "roadmap": {{
    "short_term (1-2 Years)": [
      {{
        "id": "st1", "icon": "🎯", "title": "Master [Advanced Skill/Tool]",
        "description": "Elevate proficiency in [Skill/Tool] via [Specific Course/Cert] and implement in a complex portfolio project like [Project Idea]. Focus on [Specific Concept].",
        "resources": [
            {{"title": "[Specific Course/Cert Name]", "url": "[VALID_URL_if_found_else_omit_or_#]"}},
            {{"title": "[Relevant Documentation/Book Title]", "url": "[VALID_URL_if_found_else_omit_or_#]"}}
        ]
      }},
      // ... other short term goals following the same resource URL emphasis ...
       {{
        "id": "st_example", "icon": "📚", "title": "Acquire Foundational [New Skill]",
        "description": "Gain knowledge in [New Skill, e.g., Kubernetes] via course, deploy simple app.",
        "resources": [
            {{"title": "Introductory Kubernetes Course (e.g., KodeKloud/Udemy)", "url": "[VALID_URL_if_found_else_omit_or_#]"}},
            {{"title": "Kubernetes Official Documentation", "url": "https://kubernetes.io/docs/home/"}} // Example of a good link
         ]
      }}
    ],
    "mid_term (3-5 Years)": [
        // ... mid term goals following the same resource URL emphasis ...
        {{
            "id": "mt_example", "icon": "⭐", "title": "Achieve [Key Certification]",
            "description": "Obtain [Specific Certification, e.g., AWS Certified DevOps Engineer - Professional].",
            "resources": [
                {{"title": "[Certification Provider Website]", "url": "[VALID_URL_to_cert_page]"}},
                {{"title": "[Recommended Study Guide/Platform]", "url": "[VALID_URL_if_found_else_omit_or_#]"}}
             ]
        }}
    ],
    "long_term (5+ Years)": [
        // ... long term goals following the same resource URL emphasis ...
    ]
  }},
  "key_skills_to_develop": [
      {{"category": "Technical Expertise", "skills": [ /* ... skills ... */ ]}},
      {{"category": "Leadership & Soft Skills", "skills": [ /* ... skills ... */ ]}}
  ]
}}
Resume:
{resume_text}
```"""
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "recommended_focus_area" in result and "roadmap" in result:
            return result
        else:
             st.error("AI response for roadmap missing expected structure.")
             print(f"RAW AI ROADMAP RESPONSE:\n{response.text.strip()}")
             return {"error": "Invalid structure", "raw_text": response.text.strip() if response and response.text else "No content."}
    except Exception as e:
        st.error(f"Error generating career roadmap: {str(e)}")
        st.exception(e)
        return None