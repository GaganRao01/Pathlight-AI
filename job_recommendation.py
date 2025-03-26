# job_recommendation.py
import streamlit as st
import google.generativeai as genai
from utils import extract_text
import re
import json

def generate_job_recommendation_and_roadmap(model, user_input):
    """Generates a job role recommendation and roadmap, with detailed explanations."""

    prompt = f"""
You are a career advisor providing expert, personalized guidance. Your task is to create a
detailed and actionable career roadmap based on the user's input. The user input can be
anything from a full resume to a simple statement of career interests.

Output a JSON object, and NOTHING ELSE. The JSON must be strictly valid and parsable by
Python's `json.loads()` function.

Here's the REQUIRED JSON structure:

```json
{{
  "recommended_role": "<Specific job role>",
  "justification": "<A paragraph explaining WHY this role is a good fit, referencing the user input>",
  "roadmap": {{
    "short_term": [
      {{"title": "<Goal Title 1>", "description": "<A detailed, multi-sentence description of the goal, explaining WHY it's important and HOW to achieve it.>", "resources": [{{"title": "<Resource 1>", "url": "<URL 1>"}}, {{"title": "<Resource 2>", "url": "<URL 2>"}}]}},
      {{"title": "<Goal Title 2>", "description": "<Detailed description>", "resources": [{{"title": "<Resource 3>", "url": "<URL 3>"}}]}},
      {{"title": "<Goal Title 3>", "description": "<Detailed description>", "resources": []}}
    ],
    "mid_term": [
      {{"title": "<Goal Title 1>", "description": "<A detailed, multi-sentence description>", "resources": [{{"title": "<Resource 1>", "url": "<URL 1>"}}]}},
      {{"title": "<Goal Title 2>", "description": "<Detailed description>", "resources": []}}
    ],
    "long_term": [
       {{"title": "<Goal Title 1>", "description": "<A detailed, multi-sentence description>", "resources": []}},
       {{"title": "<Goal Title 2>", "description": "<Detailed description>", "resources": [{{"title": "<Resource 1>", "url": "<URL 1>"}}]}}
    ],
    "skills_technologies": [
        {{"skill_area": "<e.g., Programming Languages>", "skills": ["<Skill 1: detailed description>", "<Skill 2: detailed description>", "<Skill 3: detailed description>"]}},
        {{"skill_area": "<e.g., Machine Learning Frameworks>", "skills": ["<Framework 1: detailed description>", "<Framework 2: detailed description>"]}},
        {{"skill_area": "<e.g., Cloud Platforms>", "skills": ["<Platform 1: detailed description>", "<Platform 2: detailed description>"]}}
    ]
  }},
  "certifications": [
    {{"title": "<Certification Title 1>", "description": "<A detailed, multi-sentence description of the certification, its benefits, and who it's for.>", "url": "<Link>"}},
    {{"title": "<Certification Title 2>", "description": "<Detailed description>", "url": "<Link>"}}
  ],
  "projects": [
    {{"level": "Beginner", "title": "<Project Title 1>", "description": "<A detailed, multi-sentence description. Explain what the project involves, what technologies are used, and what the user will learn.>", "technologies": ["<Tech 1>", "<Tech 2>"], "url": "<Optional link>"}},
    {{"level": "Intermediate", "title": "<Project Title 2>", "description": "<Detailed description>", "technologies": ["<Tech 1>", "<Tech 2>", "<Tech 3>"], "url": "<Optional link>"}},
    {{"level": "Advanced", "title": "<Project Title 3>", "description": "<Detailed description>", "technologies": ["<Tech 1>", "<Tech 2>", "<Tech 3>", "<Tech 4>"], "url": "<Optional link>"}}
  ]
}}

INSTRUCTIONS:

Be VERY specific: Don't just say "Learn Python." Say "Achieve fluency in Python, including libraries like NumPy, Pandas, and Scikit-learn. Focus on object-oriented programming and data structures."

Provide multiple goals/skills/etc.: For each section (short-term, mid-term, etc.), include at least two or three distinct items.

Detailed Descriptions: Each goal, skill, certification, and project description should be several sentences long, providing context and explaining why it's important and how to achieve it.

Working URLs: Ensure all provided URLs are valid and point to relevant resources.

JSON Only: The output must be ONLY the JSON, with no surrounding text.

Speak Directly: Use "you" and "your."

User Input:

{user_input}"""

    try:
        response = model.generate_content(prompt)
        json_match = re.search(r"{.*}", response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            st.error("Could not extract JSON from Gemini's response.")
            return None

    except Exception as e:
        st.error(f"Error generating job recommendation and roadmap: {e}")
        st.write(response.text)
        return None