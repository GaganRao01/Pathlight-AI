# ats_optimization.py (Part 1/2 - Fixed Contact Info Regex)
import streamlit as st
import re
import spacy
from analysis import get_spacy_model, get_hf_model_and_tokenizer, calculate_hybrid_score, get_resume_enhancement_suggestions # Import enhancement function
from utils import clean_and_parse_json, extract_text, preprocess_text, get_synonyms
import PyPDF2
import json # Ensure json is imported
import logging # Import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- AI-Powered Check Functions (Keep As Is) ---

def check_spelling_grammar_ai(resume_text, model):
    """Checks for spelling and grammar errors using AI and suggests corrections."""
    if not model: return {"errors": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the following resume text for spelling and grammatical errors.
    Identify specific errors and provide the corrected version for each.
    Focus on clear mistakes, not stylistic preferences. If no errors are found, return an empty list for "errors".

    Return ONLY a JSON object in the following format:
    {{
      "errors": [
        {{
          "original": "<sentence or phrase with error>",
          "corrected": "<corrected sentence or phrase>",
          "explanation": "<brief explanation of the error>"
        }},
        ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "errors" in result:
            if not result["errors"]:
                return {"errors": [], "message": "No significant spelling or grammar errors found."}
            return result
        else:
            logging.warning("AI response for grammar check was not perfectly formatted.")
            return {"errors": [], "message": "Could not definitively determine grammar errors due to AI response format."}
    except Exception as e:
        logging.error(f"AI Error (Spelling/Grammar): {e}")
        return {"errors": [], "message": f"Error during AI grammar check: {e}"}


def check_repetition_ai(resume_text, model):
    """Checks for repeated words using AI and suggests alternatives."""
    if not model: return {"repeated_words": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the following resume text for frequently repeated words (excluding common stop words like 'the', 'a', 'is', 'in').
    For each significantly repeated word (e.g., used 3 or more times), list the word, its count, and suggest 2-3 diverse synonyms or alternative phrasings appropriate for a resume context.

    Return ONLY a JSON object in the following format:
    {{
      "repeated_words": [
        {{
          "word": "<repeated word>",
          "count": <number of times repeated>,
          "suggestions": ["<alternative 1>", "<alternative 2>", "<alternative 3>"]
        }},
        ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "repeated_words" in result:
             if not result["repeated_words"]:
                return {"repeated_words": [], "message": "No significant word repetition found."}
             return result
        else:
            logging.warning("AI response for repetition check was not perfectly formatted.")
            return {"repeated_words": [], "message": "Could not definitively determine word repetition due to AI response format."}

    except Exception as e:
        logging.error(f"AI Error (Repetition): {e}")
        return {"repeated_words": [], "message": f"Error during AI repetition check: {e}"}


def check_quantify_impact_ai(resume_text, model):
    """Identifies bullet points lacking quantification using AI and suggests improvements."""
    if not model: return {"lacking_quantification": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the bullet points (lines typically starting with '*') in the experience and projects sections of the following resume text.
    Identify bullet points that lack quantifiable results or metrics (e.g., numbers, percentages, dollar amounts, specific scale).
    For each such bullet point, provide the original text and a suggestion on *how* it could be quantified or made more impactful, even if specific numbers aren't available in the text (e.g., suggest *what kind* of metric to add).

    Return ONLY a JSON object in the following format:
    {{
      "lacking_quantification": [
        {{
          "bullet": "<original bullet point text>",
          "suggestion": "<specific suggestion to add impact/quantification>"
        }},
        ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "lacking_quantification" in result:
            if not result["lacking_quantification"]:
                return {"lacking_quantification": [], "message": "Good job! Most bullet points seem to include quantifiable impact or are descriptive where appropriate."}
            return result
        else:
            logging.warning("AI response for quantification check was not perfectly formatted.")
            return {"lacking_quantification": [], "message": "Could not definitively analyze quantification due to AI response format."}
    except Exception as e:
        logging.error(f"AI Error (Quantify Impact): {e}")
        return {"lacking_quantification": [], "message": f"Error during AI quantification check: {e}"}


def check_long_bullets_ai(resume_text, model):
    """Identifies long bullet points using AI and suggests shortening."""
    if not model: return {"long_bullets": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the bullet points (lines typically starting with '*') in the following resume text.
    Identify bullet points that are too long (e.g., more than 2-3 lines of text or roughly 50 words).
    For each long bullet point, provide the original text and suggest how to make it more concise or split it into multiple points.

    Return ONLY a JSON object in the following format:
    {{
      "long_bullets": [
        {{
          "bullet": "<original long bullet point text>",
          "suggestion": "<suggestion to shorten or split>"
        }},
        ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "long_bullets" in result:
            if not result["long_bullets"]:
                 return {"long_bullets": [], "message": "No overly long bullet points found."}
            return result
        else:
            logging.warning("AI response for long bullets check was not perfectly formatted.")
            return {"long_bullets": [], "message": "Could not definitively analyze bullet length due to AI response format."}
    except Exception as e:
        logging.error(f"AI Error (Long Bullets): {e}")
        return {"long_bullets": [], "message": f"Error during AI long bullet check: {e}"}


def check_active_voice_ai(resume_text, model):
    """Identifies passive voice using AI and suggests active voice alternatives."""
    if not model: return {"passive_sentences": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the sentences in the following resume text, particularly within the experience and project descriptions.
    Identify sentences written in passive voice.
    For each passive sentence found, provide the original sentence and rewrite it in active voice, maintaining the original meaning.

    Return ONLY a JSON object in the following format:
    {{
      "passive_sentences": [
        {{
          "original": "<original passive voice sentence>",
          "active": "<rewritten active voice sentence>"
        }},
        ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "passive_sentences" in result:
            if not result["passive_sentences"]:
                 return {"passive_sentences": [], "message": "Good use of active voice detected."}
            return result
        else:
            logging.warning("AI response for active voice check was not perfectly formatted.")
            return {"passive_sentences": [], "message": "Could not definitively analyze active voice due to AI response format."}
    except Exception as e:
        logging.error(f"AI Error (Active Voice): {e}")
        return {"passive_sentences": [], "message": f"Error during AI active voice check: {e}"}


def check_hobbies_ai(resume_text, model):
    """Checks for a hobbies/interests section using AI and provides suggestions."""
    if not model: return {"found": False, "analysis": "AI model not available.", "suggestions": []}
    prompt = f"""
    Analyze the following resume text to see if it includes a section dedicated to hobbies, interests, volunteering, or similar personal activities.

    1. State whether such a section was found (true/false).
    2. If found, briefly comment on its relevance or presentation.
    3. If not found, suggest adding such a section and provide 3-5 diverse examples of hobbies/interests suitable for a professional resume (e.g., Reading, Mentoring, Photography, Playing a musical instrument, Contributing to open-source projects, Marathon running, Volunteering for [Cause]).

    Return ONLY a JSON object in the following format:
    {{
      "found": <true_or_false>,
      "analysis": "<Brief analysis if found, or 'Section not found.' if not>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...] // Only if not found
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        response = model.generate_content(prompt)
        result = clean_and_parse_json(response.text)
        if result and "found" in result:
            if result["found"] and "suggestions" not in result: result["suggestions"] = []
            elif not result["found"] and "suggestions" not in result: result["suggestions"] = ["Consider adding a 'Hobbies' or 'Interests' section."]
            return result
        else:
             logging.warning("AI response for hobbies check was not perfectly formatted.")
             return {"found": False, "analysis": "Could not determine presence of hobbies section due to AI response format.", "suggestions": ["Consider adding a 'Hobbies' or 'Interests' section."]}
    except Exception as e:
        logging.error(f"AI Error (Hobbies): {e}")
        return {"found": False, "analysis": f"Error during AI hobbies check: {e}", "suggestions": []}


# --- Standard Check Functions ---

def check_parse_rate(resume_text):
    """Simulates ATS parsing and returns a percentage."""
    total_chars = len(resume_text)
    if total_chars == 0: return 0
    non_whitespace_chars = len(re.findall(r'\S', resume_text))
    penalty = 0
    if '\t' in resume_text: penalty += 5
    if re.search(r'\s{3,}', resume_text): penalty += 5
    lines = resume_text.splitlines()
    lines_with_multiple_spaces = sum(1 for line in lines if re.search(r'\S\s{3,}\S', line))
    if lines_with_multiple_spaces > 5: penalty += 10
    parse_rate = max(0, round(((non_whitespace_chars / total_chars) * 100 if total_chars > 0 else 0) - penalty))
    return min(parse_rate, 99)


def check_resume_length(resume_text):
    """Checks resume length (word count)."""
    word_count = len(resume_text.split())
    if word_count == 0: return "Resume is empty.", 0
    elif word_count < 350: return "Resume is likely too short. Consider adding more detail.", word_count
    elif word_count > 800: return "Resume might be too long. Aim for conciseness (1 page, or 2 for extensive experience).", word_count
    else: return "Resume length is generally within the optimal range.", word_count

def check_buzzwords(resume_text):
    """Checks for common buzzwords/cliches."""
    buzzwords = [
        "results-driven", "team player", "detail-oriented", "go-getter", "synergy", "leverage",
        "proactive", "dynamic", "self-starter", "thought leader", "goal-oriented", "hardworking",
        "motivated", "passionate", "strategic thinker", "out-of-the-box", "think outside the box",
        "value add", "impactful"
    ]
    found_buzzwords = []
    text_lower = resume_text.lower()
    for buzzword in buzzwords:
        if re.search(r'\b' + re.escape(buzzword) + r'\b', text_lower):
            found_buzzwords.append(buzzword)
    return found_buzzwords

# --- FIXED check_contact_information ---
def check_contact_information(resume_text):
    """Checks for presence and format of contact information with improved regex."""
    contact_info = {}
    lines = resume_text.splitlines()
    text_lower = resume_text.lower()

    # --- Phone ---
    # Look near keywords or common patterns
    phone_match = re.search(r'(?:phone|mobile|tel\.?):?\s*([\+\(\)\d\s-]{10,})', text_lower, re.IGNORECASE)
    if phone_match:
        contact_info['phone_number'] = phone_match.group(1).strip()
    else: # Fallback to general pattern if keyword not found, but be stricter
        # Stricter pattern focusing on plausible phone number structures
        phone_match_fallback = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', resume_text)
        if phone_match_fallback:
             # Avoid matching numbers if preceded by non-space/non-contact keywords within 10 chars
             preceding_context = resume_text[max(0, phone_match_fallback.start()-15):phone_match_fallback.start()]
             if not re.search(r'\b(?:experience|project|salary|id)\b', preceding_context, re.IGNORECASE):
                contact_info['phone_number'] = phone_match_fallback.group(0).strip()


    # --- Email ---
    # Standard email regex, usually reliable
    email_match = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', resume_text)
    if email_match:
        contact_info['email_address'] = email_match.group(0).strip()
        # Check for unprofessional domains
        unprofessional_domains = ["aol.com", "yahoo.com", "hotmail.com"]
        if any(domain in contact_info['email_address'] for domain in unprofessional_domains):
             contact_info['email_warning'] = "Consider a more professional email provider (e.g., Gmail)."

    # --- LinkedIn ---
    # Prioritize URL with /in/
    linkedin_match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[\w\-\.]+\/?', resume_text, re.IGNORECASE)
    if linkedin_match:
        contact_info['linkedin_url'] = linkedin_match.group(0).strip()

    # --- Portfolio/Website/GitHub ---
    # Look for GitHub specifically first
    github_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/[\w\-\.]+\/?', resume_text, re.IGNORECASE)
    if github_match:
        contact_info['github_url'] = github_match.group(0).strip()

    # Look for other URLs, avoiding LinkedIn and email domains, and prioritizing common portfolio keywords
    portfolio_keywords = ['portfolio', 'website', 'github', 'gitlab', 'behance', 'dribbble']
    url_pattern = r'(?:https?:\/\/)?(?:www\.)?[\w\-\.]+\.(?:com|io|dev|me|net|org|ai|co|tech)\/?[\w\-\/\.]*'
    potential_urls = re.findall(url_pattern, resume_text, re.IGNORECASE)

    for url in potential_urls:
        url_lower = url.lower()
        # Skip if it's the LinkedIn URL, GitHub URL, or part of the email address
        if ('linkedin_url' in contact_info and contact_info['linkedin_url'] in url) or \
           ('github_url' in contact_info and contact_info['github_url'] in url) or \
           ('email_address' in contact_info and url_lower in contact_info['email_address']):
            continue
        # Check if it appears near a relevant keyword on the same line
        for line in lines:
             line_lower = line.lower()
             if url_lower in line_lower and any(keyword in line_lower for keyword in portfolio_keywords):
                  contact_info['portfolio_url'] = url.strip()
                  break # Found one near a keyword
        # If not found near keyword, store the first valid-looking one (basic check)
        if 'portfolio_url' not in contact_info and '.' in url and len(url) > 5:
             contact_info['portfolio_url'] = url.strip()
             # break # Uncomment if you only want the first generic URL found


    # --- Location ---
    location_str = None
    # Look for keywords first
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if 'address:' in line_lower or 'location:' in line_lower:
            # Capture text after keyword on the same line, or possibly next line(s)
            location_part = re.split(r'address:|location:', line, flags=re.IGNORECASE)[-1].strip()
            if location_part:
                location_str = location_part
                # Look ahead slightly if same line is short
                if len(location_str) < 5 and i + 1 < len(lines) and len(lines[i+1].strip()) > 0:
                     location_str += ", " + lines[i+1].strip()
                break # Found based on keyword

    # If not found via keyword, try common patterns like City, State/Country near the top
    if not location_str:
         for line in lines[:5]: # Check near the top
             # Pattern: Word(s), Word(s) - more constrained
             loc_match = re.search(r'\b([A-Z][a-zA-Z\s\.-]+?),\s*([A-Z][a-zA-Z\s\.-]+)\b', line)
             if loc_match:
                  potential_loc = loc_match.group(0).strip()
                  # Basic sanity check - avoid all caps, short strings, known non-locations
                  if not potential_loc.isupper() and len(potential_loc) > 5 and 'PROFILE' not in potential_loc and 'OBJECTIVE' not in potential_loc:
                       location_str = potential_loc
                       break

    if location_str:
        # Final cleanup - remove potential noise if it looks very unlike a location
        if location_str.isupper() and len(location_str) < 15: # Likely a heading
             pass # Discard likely heading
        elif len(re.findall(r'\d', location_str)) > 6 and len(location_str) < 20: # Too many digits for just city/state
             pass # Discard likely ID or code
        else:
             contact_info['location'] = location_str.strip()


    return contact_info


def check_essential_sections(resume_text):
    text_lower = resume_text.lower()
    sections_found = []
    # Use regex with word boundaries and potential variations
    if re.search(r'\b(skills?|technical skills?|proficiencies)\b', text_lower): sections_found.append("Skills")
    if re.search(r'\b(experience|work experience|professional experience|employment history)\b', text_lower): sections_found.append("Experience")
    if re.search(r'\b(education|academic background|qualifications)\b', text_lower): sections_found.append("Education")
    if re.search(r'\b(summary|profile|objective|about me?)\b', text_lower): sections_found.append("Summary/Profile/Objective")

    missing_sections = []
    # Ensure core sections are present by checking the found list
    if "Skills" not in sections_found: missing_sections.append("Skills")
    if "Experience" not in sections_found: missing_sections.append("Experience")
    if "Education" not in sections_found: missing_sections.append("Education")
    # Allow either Summary OR Objective OR Profile
    if "Summary/Profile/Objective" not in sections_found: missing_sections.append("Summary/Profile/Objective")

    return sections_found, missing_sections


# --- Layout Analysis (Keep As Is) ---
def analyze_resume_layout(resume_file):
    layout_issues = []
    formatting_score = 100
    try:
        resume_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(resume_file)
        num_pages = len(pdf_reader.pages)

        if num_pages == 0:
             logging.error("Could not read PDF pages.")
             return {"num_pages": 0, "layout_issues": ["Could not read PDF pages."], "formatting_score": 0}
        elif num_pages > 2:
            layout_issues.append(f"Resume is {num_pages} pages long. Aim for 1-2 pages max.")
            formatting_score -= 15
        elif num_pages == 2:
             layout_issues.append("Resume is 2 pages. Ensure this is necessary and prioritize key info on page 1.")
             formatting_score -= 5

        full_text = ""
        try:
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text: full_text += page_text + "\n"
        except Exception as text_extract_error:
             layout_issues.append(f"Could not fully extract text for layout analysis: {text_extract_error}")
             formatting_score -= 10

        layout_issues.append("Check for consistent font usage (1-2 professional fonts recommended).")
        formatting_score -= 5 # Assume potential issue
        if re.search(r"\n\s*\n\s*\n", full_text):
            layout_issues.append("Excessive vertical whitespace detected.")
            formatting_score -= 5
        if re.search(r" {3,}", full_text):
             layout_issues.append("Avoid using multiple spaces for alignment; use standard indentation.")
             formatting_score -= 5
        layout_issues.append("Ensure margins are adequate (0.5 - 1 inch).")
        formatting_score -= 5 # Assume potential issue
        layout_issues.append("Avoid complex tables, columns, images, or graphics for best ATS compatibility.")
        formatting_score -= 10

        formatting_score = max(0, formatting_score)
        return {"num_pages": num_pages, "layout_issues": layout_issues, "formatting_score": formatting_score}

    except Exception as e:
        logging.error(f"Error analyzing PDF layout: {str(e)}", exc_info=True)
        resume_file.seek(0)
        return {"num_pages": "N/A", "layout_issues": [f"Error during layout analysis: {e}"], "formatting_score": 0}

# --- End of Part 1/2 ---
# ats_optimization.py (Part 2/2 - Fixed Contact Info Regex)

# --- Main ATS Optimization Function ---
def get_ats_optimization_results(resume_text, resume_file, match_analysis=None, model=None):
    """Main function to perform all ATS optimization checks."""
    logging.info("Starting ATS Optimization process.")
    # Load spaCy model only if needed for standard checks (currently not strictly required by them)
    # nlp_model = get_spacy_model()

    if not model:
         logging.error("Gemini AI model is not available for ATS checks.")
         st.error("Gemini AI model is not available. Cannot perform AI-driven checks.")
         # Return a structure indicating failure but allowing display function to handle it
         return {
             "ai_checks": {
                 "spelling_grammar": {"errors": [], "message": "AI model unavailable."},
                 "repetition": {"repeated_words": [], "message": "AI model unavailable."},
                 "quantify_impact": {"lacking_quantification": [], "message": "AI model unavailable."},
                 "long_bullets": {"long_bullets": [], "message": "AI model unavailable."},
                 "active_voice": {"passive_sentences": [], "message": "AI model unavailable."},
                 "hobbies": {"found": False, "analysis": "AI model unavailable.", "suggestions": []},
             },
             "standard_checks": {}, # Standard checks might still run below
             "layout_analysis": {},
             "enhancement_suggestions": {}
         }

    # --- Perform AI Checks ---
    logging.info("Running AI-powered ATS checks...")
    # Using st.spinner here might be less ideal if called from main.py which already has spinners
    # Consider just logging start/end or passing spinner context if needed.
    spelling_grammar_results = check_spelling_grammar_ai(resume_text, model)
    repetition_results = check_repetition_ai(resume_text, model)
    quantify_results = check_quantify_impact_ai(resume_text, model)
    long_bullet_results = check_long_bullets_ai(resume_text, model)
    active_voice_results = check_active_voice_ai(resume_text, model)
    hobbies_results = check_hobbies_ai(resume_text, model)
    logging.info("AI checks completed.")

    # --- Run Enhancement Suggestions (uses AI) ---
    logging.info("Running AI enhancement suggestions...")
    enhancements = get_resume_enhancement_suggestions(model, resume_text, match_analysis)
    logging.info("Enhancement suggestions completed.")

    # --- Perform Standard Checks ---
    logging.info("Running standard ATS checks...")
    parse_rate = check_parse_rate(resume_text)
    length_feedback, word_count = check_resume_length(resume_text)
    buzzwords_found = check_buzzwords(resume_text)
    contact_info = check_contact_information(resume_text) # Use the fixed function
    essential_sections_found, essential_sections_missing = check_essential_sections(resume_text)
    logging.info("Standard checks completed.")

    # --- Perform Layout Analysis ---
    logging.info("Running layout analysis...")
    layout_analysis_results = analyze_resume_layout(resume_file) # Needs the file object
    logging.info("Layout analysis completed.")


    # --- Combine Results ---
    results = {
        "ai_checks": {
             "spelling_grammar": spelling_grammar_results if spelling_grammar_results else {"errors": [], "message": "Check failed or incomplete."},
             "repetition": repetition_results if repetition_results else {"repeated_words": [], "message": "Check failed or incomplete."},
             "quantify_impact": quantify_results if quantify_results else {"lacking_quantification": [], "message": "Check failed or incomplete."},
             "long_bullets": long_bullet_results if long_bullet_results else {"long_bullets": [], "message": "Check failed or incomplete."},
             "active_voice": active_voice_results if active_voice_results else {"passive_sentences": [], "message": "Check failed or incomplete."},
             "hobbies": hobbies_results if hobbies_results else {"found": False, "analysis": "Check failed or incomplete.", "suggestions": []},
        },
        "standard_checks": {
            "parse_rate": parse_rate,
            "resume_length_feedback": length_feedback,
            "resume_word_count": word_count,
            "buzzwords": buzzwords_found,
            "contact_information": contact_info, # Includes fixed results
            "essential_sections_found": essential_sections_found,
            "essential_sections_missing": essential_sections_missing,
        },
        "layout_analysis": layout_analysis_results if layout_analysis_results else {"num_pages": "N/A", "layout_issues": ["Analysis failed."], "formatting_score": 0},
        "enhancement_suggestions": enhancements if enhancements else {"message": "Enhancement suggestions failed or were not generated."} # Provide default structure
    }
    logging.info("ATS Optimization results compiled.")

    # Log the structure of the contact info found for debugging
    logging.debug(f"Contact info check results: {contact_info}")

    return results

# --- End of ats_optimization.py ---