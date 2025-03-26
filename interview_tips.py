# interview_tips.py (Revised for Deeper Personalization)

import streamlit as st
import json
import re
# Assuming these are available and working correctly
# from analysis import calculate_hybrid_score, get_hf_model_and_tokenizer, get_spacy_model # Likely not needed now
from utils import clean_and_parse_json

def generate_interview_tips(model, resume_text, job_description):
    """
    Generates highly personalized interview tips and potential questions,
    deeply integrating resume and job description specifics.
    """

    prompt = f"""
Act as an expert interview coach preparing a candidate specifically for an interview for the **[Job Title - Extract from JD if possible, otherwise use 'role below']** position at **[Company Name - Extract from JD if possible]**, based *only* on their provided RESUME and the JOB DESCRIPTION. Generate highly specific, actionable advice and *potential* interview questions tailored precisely to this candidate and this role.

**CRITICAL INSTRUCTIONS:**

*   **HYPER-PERSONALIZATION:** ALL generated content (tips, questions, response outlines) MUST directly reference specific skills, projects, achievements, technologies, or experiences found in the candidate's RESUME and link them explicitly to the requirements, responsibilities, or company context mentioned in the JOB DESCRIPTION. Avoid generic advice AT ALL COSTS.
*   **FOCUS ON THE GAP & MATCH:** Analyze the alignment and potential gaps between the resume and job description. Generate questions interviewers might ask to probe these areas. Suggest ways the candidate can leverage their strengths (from RESUME) to address potential weaknesses relative to the JD.
*   **BEHAVIORAL QUESTIONS (STAR Method):** For behavioral questions, DO NOT just list questions. For each question, suggest **specific examples or projects from the candidate's RESUME** that would be suitable for constructing a STAR (Situation, Task, Action, Result) answer. Guide them on *what aspects* of that experience to highlight.
*   **TECHNICAL QUESTIONS (Potential & Specific):** Generate *potential* technical questions based on the **key technical requirements listed in the JOB DESCRIPTION**. Frame these questions to probe the candidate's depth of knowledge, referencing relevant skills or projects mentioned in their RESUME. Suggest response strategies, including how to handle questions where their experience (from RESUME) might be limited but related.
*   **ACTIONABLE & CONCRETE:** Response outlines should provide tangible points, keywords, or specific resume achievements the candidate should mention.
*   **STRUCTURED JSON:** Output ONLY a valid JSON object in the specified format. No extra text, markdown, or explanations outside the JSON structure.

**JSON FORMAT:**

```json
{{
  "preparation_focus_areas": [ // High-level strategy based on comparison
    {{
      "area": "Leverage Strength in [Key Skill/Area from Resume]",
      "action": "Prepare multiple examples showcasing your expertise in [Key Skill/Area], connecting it directly to how it fulfills [Requirement X and Y] from the job description. Quantify impact where possible using data from your [Resume Section, e.g., Project Z] description."
    }},
    {{
      "area": "Address Potential Gap in [Skill/Tech from JD, less prominent in Resume]",
      "action": "Be ready to discuss how your experience with [Related Skill/Project from Resume] provides transferable knowledge. Highlight your learning agility and mention any proactive steps taken (e.g., 'I've been exploring [Specific Tech] through [Platform/Course]'). Frame your existing skills as a strong foundation."
    }},
    {{
      "area": "Demonstrate Company Fit",
      "action": "Review [Company Name]'s mission/values mentioned in the JD or easily found online. Prepare talking points on how your experience at [Previous Company] or your work on [Relevant Project] aligns with their focus on [Company Value/Goal, e.g., innovation, customer focus]."
    }}
  ],
  "resume_deep_dive_prompts": [ // Things interviewer might ask specifically about the resume
    {{
      "prompt": "Your resume mentions achieving [Quantifiable Result] on the [Project Name] project. Can you walk me through the steps you took and the specific challenges you overcame?",
      "advice": "Use the STAR method. Focus on *your* specific actions, the tools used (e.g., [Tool from Resume]), and clearly explain how you measured the result.",
      "resume_reference": "[Project Name] / [Specific Bullet Point]"
    }},
    {{
      "prompt": "You list [Specific Skill/Tool] on your resume. How have you applied it in a professional setting, perhaps during your time at [Previous Company]?",
      "advice": "Provide a concrete example. Describe the task, how you used the skill/tool, and the outcome. Avoid generic descriptions.",
      "resume_reference": "Skills Section / Experience at [Previous Company]"
    }}
    // Add 1-2 more specific resume prompts
  ],
  "potential_behavioral_questions": [
    {{
      "question": "Describe a time you had to learn a new technology or complex process quickly.",
      "resume_example_source": "Look at projects involving new tech listed on the resume, like [Project Name] or transitions between roles. Could also relate to certifications obtained.",
      "suggested_star_points": {{
        "Situation": "Project kickoff requiring [New Technology from Resume/JD] at [Company].",
        "Task": "Needed to become proficient quickly to contribute to [Project Goal].",
        "Action": "Mention specific actions: 'Dedicated evenings to [Online Course/Docs]', 'Paired with [Colleague]', 'Built small proof-of-concept using [Tool]'.",
        "Result": "Highlight successful contribution: 'Was able to effectively [Action Verb] using the new tech within [Timeframe], contributing to the project's success by [Measure].'"
      }}
    }},
    {{
      "question": "Tell me about a significant challenge you faced during the [Project Name from Resume] project and how you resolved it.",
      "resume_example_source": "Directly reference the [Project Name] entry.",
      "suggested_star_points": {{
        "Situation": "Describe the specific challenge encountered (e.g., unexpected technical issue, scope change, resource constraint).",
        "Task": "What was the objective despite the challenge?",
        "Action": "Detail *your* problem-solving steps: 'I analyzed [X], proposed [Solution Y], collaborated with [Team Z]...'. Mention skills like 'problem-solving', 'collaboration'.",
        "Result": "Explain the resolution and positive outcome: 'Successfully overcame the obstacle, delivering the project [On Time/Within Budget/With X Improvement]'."
      }}
    }}
    // Add 1-2 more behavioral questions linked to resume themes (e.g., teamwork, initiative)
  ],
  "potential_technical_questions": [ // Directly tied to JD requirements & Resume skills
    {{
      "question": "The job requires experience with [Key Tech from JD, e.g., 'Kubernetes']. Your resume lists [Related Skill/Tool, e.g., 'Docker']. Can you explain your understanding of Kubernetes orchestration and how your Docker experience relates?",
      "advice": "Acknowledge your specific Kubernetes experience level honestly. Bridge the gap: Explain Docker fundamentals (containerization) and how they relate to Kubernetes' purpose (orchestration at scale). Mention any theoretical knowledge, tutorials, or personal projects (even basic ones) involving Kubernetes. Express strong interest in deepening Kubernetes skills.",
      "resume_reference": "Skills: [Docker], JD Requirement: [Kubernetes]"
    }},
    {{
      "question": "How would you approach troubleshooting a performance issue in a system like the one described in the [Resume Project involving relevant architecture, e.g., RAG pipeline project]?",
      "advice": "Outline a systematic approach: 1. Define/Measure the 'slowness' (metrics, user impact). 2. Isolate the bottleneck (profiling code, checking infrastructure - DB queries, network latency, specific components like the LLM calls in the RAG example). 3. Hypothesize causes. 4. Test hypotheses (load testing, specific component tests). 5. Implement and verify fix. Mention relevant tools from resume if applicable.",
      "resume_reference": "[Relevant Project], Skills section"
    }}
    // Add 1-2 more technical questions based on core JD skills/responsibilities
  ],
  "questions_candidate_should_ask": [ // Make them specific to THIS opportunity
    {{
      "question": "Considering my background in [Specific Area from Resume, e.g., 'building RAG pipelines'], what specific project or challenge might I tackle first in this role to make an immediate impact?",
      "purpose": "Shows proactive thinking and links your specific skills to their needs."
    }},
    {{
      "question": "How does the team collaborate on [Specific Process Mentioned in JD, e.g., 'model deployment']? What tools and workflows are typically used?",
      "purpose": "Demonstrates interest in team dynamics and practical aspects of the role."
    }},
    {{
      "question": "What does success look like in this role after the first year, particularly concerning the responsibilities around [Key Responsibility from JD]?",
      "purpose": "Shows focus on performance and understanding expectations."
    }}
    // Add 1 more relevant question
  ]
}}
Job Description:
{job_description}
Resume:
{resume_text}
"""
    try:
        # generation_config = {"temperature": 0.5, "max_output_tokens": 2000}
        response = model.generate_content(
            prompt,
            # generation_config=generation_config
        )
        # Use the robust JSON cleaner/parser
        result = clean_and_parse_json(response.text)
        return result
    except Exception as e:
        st.error(f"Error generating interview tips: {str(e)}")
        # Optionally log the prompt
        # print("--- PROMPT FAILED ---")
        # print(prompt)
        # print("--- END PROMPT ---")
        return None