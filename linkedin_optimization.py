# linkedin_optimization.py (Corrected Prompt Definition + Retry Logic)

import streamlit as st
import json
import re
import logging # Import logging
# Assuming these are available and working correctly
# from analysis import calculate_hybrid_score, get_spacy_model, get_hf_model_and_tokenizer # Not strictly needed
from utils import clean_and_parse_json # Import the robust parser
import time # Import time for potential delays

# Setup logger if not already done
# Ensure logging is configured in main.py or here if run standalone
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_linkedin_optimization(model, resume_text):
    """
    Generate detailed, actionable LinkedIn profile optimization suggestions
    based on the resume, with retry logic for JSON parsing errors.
    """

    prompt = f"""
Act as an expert LinkedIn profile coach and personal branding specialist. Analyze the provided resume thoroughly and generate highly specific, actionable, and personalized suggestions to optimize a LinkedIn profile based *only* on this resume content. Assume the user wants to attract recruiters and showcase their expertise effectively for roles related to their resume.

**Instructions:**

*   **Be Specific & Actionable:** Provide concrete examples, suggest alternative phrasing, and explain *why* each change is beneficial. Don't just say "improve headline"; provide 2-3 strong headline examples based on the resume's keywords and experience.
*   **Connect to Resume:** Directly reference skills, experiences, achievements, and keywords found in the resume when making suggestions.
*   **Modern Practices:** Incorporate current LinkedIn best practices (e.g., keyword optimization, quantifiable results, storytelling in 'About', skill endorsements).
*   **Structured JSON Output:** Return ONLY a valid JSON object in the exact format below.
    *   **CRITICAL SYNTAX:** Ensure all strings are properly escaped (e.g., use \\" inside strings). Ensure commas (,) correctly separate all elements in lists and all key-value pairs in objects (except the very last one in each list/object). Pay meticulous attention to braces {{}}, brackets [], colons :, and quotes "".
    *   No introductory text, explanations outside the JSON, or markdown formatting.

**JSON Format:**

```json
{{
  "headline_suggestions": [
    {{
      "headline": "<Headline Example 1 - Keyword-rich, highlighting key role/skills from resume>",
      "rationale": "This headline uses keywords like [Keyword1], [Keyword2] relevant to your experience in [Field/Role] and clearly states your value."
    }},
    {{
      "headline": "<Headline Example 2 - Different focus, e.g., specific achievement or specialization>",
      "rationale": "Focuses on your specialization in [Specialization] mentioned in your [Resume Section] section."
    }},
    {{
      "headline": "<Headline Example 3 - Concise alternative>",
      "rationale": "A concise option emphasizing core skills like [Skill1] and [Skill2]."
    }}
  ],
  "about_section_suggestions": [
    {{
      "type": "Opening Hook",
      "suggestion": "Start with a strong opening sentence summarizing your core expertise and career focus based on the resume. E.g., 'Results-driven [Your Role, e.g., AI Engineer] with X years of experience in [Key Area 1] and [Key Area 2], passionate about leveraging [Specific Technology/Skill] to solve complex challenges in [Industry].'",
      "resume_reference": "Overall resume focus, summary section if present."
    }},
    {{
      "type": "Elaborate on Experience/Achievements",
      "suggestion": "Dedicate a paragraph to expand on 1-2 major achievements mentioned in your resume's experience section. Use storytelling: Briefly describe the challenge, your actions (using strong verbs), and the quantifiable results. E.g., 'At [Company], I spearheaded the [Project Name] initiative, which involved [Action 1] and [Action 2], resulting in a [Quantifiable Result like % increase, $ saved].'",
      "resume_reference": "Experience section, specific project/achievement bullet points."
    }},
    {{
      "type": "Keyword Integration",
      "suggestion": "Naturally weave in keywords relevant to your field found in the resume, such as [Keyword1], [Keyword2], [Technology1], [Methodology1]. Ensure the text flows well and isn't just keyword stuffing.",
      "resume_reference": "Skills section, Experience descriptions."
    }},
    {{
      "type": "Showcase Passion/Motivation",
      "suggestion": "Briefly mention your passion for your field or specific areas highlighted in the resume (e.g., 'My fascination with [Area] drives my commitment to...'). Connect this to the types of roles or companies you are targeting.",
      "resume_reference": "Summary/Objective (if present), Project descriptions."
    }},
    {{
      "type": "Call to Action (Optional)",
      "suggestion": "Consider ending with a soft call to action, inviting connections or discussions related to your expertise. E.g., 'Open to connecting with professionals in [Industry] or discussing opportunities related to [Key Skill].'",
      "resume_reference": "N/A"
    }}
  ],
  "experience_section_suggestions": [
    {{
      "job_title_company": "<Job Title at Company from Resume>",
      "suggestions": [
        "Ensure the job title matches or is a standard industry equivalent.",
        "Rewrite 2-3 key bullet points from the resume for LinkedIn. Focus on using the STAR method (Situation, Task, Action, Result) and strong action verbs.",
        "Ensure quantifiable results are prominent (e.g., 'Achieved X by doing Y, resulting in Z% improvement'). Convert resume points like '[Resume Bullet]' into a more impactful LinkedIn version: '[Improved LinkedIn Bullet]'.",
        "Incorporate relevant keywords naturally within the descriptions, such as [Keyword relevant to this job].",
        "Consider adding links to relevant projects or publications completed during this role, if applicable and mentioned in the resume."
      ],
       "resume_reference": "Specific job entry in the Experience section."
    }}
    // Add more entries for other significant roles in the resume
  ],
  "skills_section_suggestions": {{
    "skills_to_add": [
        "<List specific technical skills from resume's Skills/Experience, e.g., 'Python (Pandas, NumPy)', 'AWS (EC2, S3)', 'Machine Learning'>",
        "<List key soft skills demonstrated in resume experience, e.g., 'Project Management', 'Cross-functional Collaboration', 'Data Analysis & Reporting'>"
        // Limit to a reasonable number, e.g., top 15-20 relevant skills
      ],
    "skills_to_prioritize_endorsements": [
        "<Identify the 3-5 most critical skills for the user's target roles based on the resume.>",
        "e.g., '[Core Skill 1]', '[Core Skill 2]', '[Core Technology]'"
      ],
    "endorsement_strategy": "Actively seek endorsements for your top 3-5 skills by endorsing colleagues for their skills first, and politely requesting endorsements from connections who can genuinely vouch for your expertise in specific areas highlighted on your profile."
  }},
  "education_section_suggestions": [
    "Ensure all relevant degrees, institutions, and dates from the resume are included.",
    "Add relevant activities, societies, or honors if mentioned in the resume.",
    "Consider adding specific relevant coursework if you are a recent graduate or it directly relates to target roles."
  ],
  "additional_sections_suggestions": [
    {{
        "section_name": "Projects",
        "suggestion": "If the resume lists projects, create dedicated project entries on LinkedIn. Describe the project goal, your role, key actions, technologies used ([Tech1], [Tech2]), and outcomes/links, mirroring the resume details.",
        "resume_reference": "Projects section."
    }},
    {{
        "section_name": "Certifications",
        "suggestion": "Add all certifications listed on the resume to the 'Licenses & Certifications' section on LinkedIn. Include issuing organization and dates.",
        "resume_reference": "Certifications section."
    }}
    // Add other sections like Publications, Volunteering if relevant based on resume
  ],
  "overall_profile_tips": [
    "Customize your LinkedIn URL to be professional (e.g., linkedin.com/in/yourname).",
    "Use a professional, clear headshot photo.",
    "Ensure your profile is set to 'Public' and consider enabling 'Open to Work' features if actively job searching.",
    "Regularly engage with content and connections relevant to your industry to increase visibility."
  ]
}}
---
Resume:
{resume_text}
---
""" # <<<--- CORRECTED: Added missing closing triple quotes

    # --- Function Body (Retry Logic) ---
    max_retries = 2 # Number of times to retry after the first failure
    attempts = 0
    last_error = None
    response = None # Initialize response variable

    while attempts <= max_retries: # Use <= to include the initial try + retries
        attempts += 1
        logger.info(f"Attempt {attempts} to generate LinkedIn suggestions...")
        try:
            # Add generation config if needed, e.g., for temperature control
            # generation_config = {"temperature": 0.5}
            response = model.generate_content(
                prompt,
                # generation_config=generation_config # Uncomment if using config
            )
            # Check if response or text is potentially None or empty
            if response is None or not hasattr(response, 'text') or not response.text:
                 logger.warning(f"Attempt {attempts}: Received empty response from AI model.")
                 st.warning(f"Attempt {attempts}: Received empty response from AI model.")
                 last_error = ValueError("Empty response from AI model")
                 if attempts >= max_retries: break # Exit loop if max retries reached
                 time.sleep(0.5) # Small delay before retry
                 continue # Go to next attempt

            result = clean_and_parse_json(response.text) # Use the robust parser from utils
            if result:
                logger.info(f"Successfully generated LinkedIn suggestions on attempt {attempts}.")
                return result # Success!
            else:
                # clean_and_parse_json already displays an error via st.error
                logger.warning(f"Attempt {attempts}: Failed to parse JSON from response (clean_and_parse_json returned None).")
                st.warning(f"Attempt {attempts}: Failed to parse JSON from AI response. Retrying...")
                last_error = ValueError("Failed to parse JSON after cleaning.") # Use a generic error type
                # Log the failed raw text for debugging
                logger.debug(f"--- ATTEMPT {attempts} FAILED RAW TEXT ---\n{response.text}\n--- END FAILED RAW TEXT ---")

        except json.JSONDecodeError as json_err:
             # This might be redundant if clean_and_parse_json handles it robustly, but good safety net
             logger.warning(f"Attempt {attempts}: JSON decoding failed directly: {json_err}")
             st.warning(f"Attempt {attempts}: AI response was not valid JSON. Retrying...")
             last_error = json_err
             # Log the raw text that caused the error
             logger.debug(f"--- ATTEMPT {attempts} JSONDecodeError RAW TEXT ---\n{response.text if response and hasattr(response, 'text') else 'N/A'}\n--- END FAILED RAW TEXT ---")
        except Exception as e:
             # Catch other potential API errors or unexpected issues
             logger.error(f"Attempt {attempts}: An unexpected error occurred during generation: {str(e)}", exc_info=True)
             st.error(f"Attempt {attempts}: An unexpected error occurred: {str(e)}")
             last_error = e
             # Break on unexpected errors other than parsing unless you want to retry these too
             break

        # Wait a short time before the next attempt if it wasn't the last one
        if attempts < max_retries:
             time.sleep(0.5) # Small delay before retrying

    # If loop finishes without success after all retries
    logger.error(f"Failed to generate LinkedIn optimization suggestions after {attempts} attempts.")
    st.error(f"Failed to generate LinkedIn optimization suggestions after {attempts} attempts.")
    if last_error:
         # Show the last error encountered to the user
         st.error(f"Last error: {type(last_error).__name__}: {last_error}")
         # Optionally show the raw response if debugging is needed
         # if response and hasattr(response, 'text'):
         #    st.code(response.text, language=None)
    return None