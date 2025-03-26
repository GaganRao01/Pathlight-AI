# ats_optimization.py (Enhanced Prompts for Consistency)
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
logger = logging.getLogger(__name__)


# --- AI-Powered Check Functions (Prompts Updated) ---

def check_spelling_grammar_ai(resume_text, model):
    """Checks for spelling and grammar errors using AI and suggests corrections."""
    if not model: return {"errors": [], "message": "AI model not available."}
    # --- UPDATED PROMPT ---
    prompt = f"""
    Act as a meticulous proofreader. Analyze the *entire* following resume text THOROUGHLY for spelling and grammatical errors.
    Identify ALL specific errors you find, no matter how small. Provide the original context and the corrected version for each error identified.
    Focus on clear mistakes, not stylistic preferences. If absolutely no errors are found after careful review, return an empty list for "errors".

    Return ONLY a valid JSON object in the following format:
    {{
      "errors": [
        {{
          "original": "<sentence or phrase with error>",
          "corrected": "<corrected sentence or phrase>",
         "explanation": "<brief explanation of the error>"
        }},
        // ... include ALL errors found ...
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    # --- END UPDATED PROMPT ---
    try:
        # Explicitly set a low temperature for more deterministic output
        generation_config = {"temperature": 0.1}
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "errors" in result:
            if not result["errors"]:
                return {"errors": [], "message": "No significant spelling or grammar errors found after review."}
            # Log how many errors were found by AI
            logger.info(f"AI found {len(result['errors'])} potential spelling/grammar errors.")
            return result
        else:
            logger.warning("AI response for grammar check was not perfectly formatted or missing 'errors' key.")
            # Log the raw response if parsing failed or key missing
            logger.debug(f"RAW Grammar Check Response:\n{response.text if response else 'N/A'}")
            return {"errors": [], "message": "Could not reliably check grammar due to AI response format."}
    except Exception as e:
        logger.error(f"AI Error (Spelling/Grammar): {e}", exc_info=True)
        return {"errors": [], "message": f"Error during AI grammar check: {e}"}


def check_repetition_ai(resume_text, model):
    """Checks for repeated words using AI and suggests alternatives."""
    if not model: return {"repeated_words": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the following resume text for frequently repeated words (excluding common English stop words like 'the', 'a', 'is', 'in', 'and', 'it').
    List each word used 3 or more times, its count, and suggest 2-3 diverse synonyms or alternative phrasings appropriate for a professional resume context.

    Return ONLY a valid JSON object in the following format:
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
        # Low temperature might help consistency here too
        generation_config = {"temperature": 0.2}
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "repeated_words" in result:
             if not result["repeated_words"]:
                return {"repeated_words": [], "message": "No significant word repetition found."}
             logger.info(f"AI found {len(result['repeated_words'])} repeated words.")
             return result
        else:
            logger.warning("AI response for repetition check was not perfectly formatted or missing 'repeated_words' key.")
            logger.debug(f"RAW Repetition Check Response:\n{response.text if response else 'N/A'}")
            return {"repeated_words": [], "message": "Could not reliably check repetition due to AI response format."}

    except Exception as e:
        logger.error(f"AI Error (Repetition): {e}", exc_info=True)
        return {"repeated_words": [], "message": f"Error during AI repetition check: {e}"}


def check_quantify_impact_ai(resume_text, model):
    """Identifies bullet points lacking quantification using AI and suggests improvements."""
    if not model: return {"lacking_quantification": [], "message": "AI model not available."}
    prompt = f"""
    Analyze *all* bullet points (lines typically starting with '*' or '-') in the experience and projects sections of the following resume text.
    Identify *every* bullet point that lacks quantifiable results or metrics (e.g., numbers, percentages, dollar amounts, specific scale, user counts, efficiency gains).
    For each such bullet point identified, provide the original text and a *specific suggestion* on *how* it could be quantified or made more impactful. Suggest *what kind* of metric could be added, even if exact numbers aren't present (e.g., "Quantify the impact on user engagement," "Specify the number of team members led," "Estimate the percentage reduction").

    Return ONLY a valid JSON object in the following format:
    {{
      "lacking_quantification": [
        {{
          "bullet": "<original bullet point text>",
          "suggestion": "<specific suggestion to add impact/quantification>"
        }},
        ... // Include ALL points lacking quantification
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        generation_config = {"temperature": 0.2}
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "lacking_quantification" in result:
            if not result["lacking_quantification"]:
                return {"lacking_quantification": [], "message": "Good job! All bullet points seem to include quantifiable impact or are descriptive where appropriate."}
            logger.info(f"AI found {len(result['lacking_quantification'])} bullets lacking quantification.")
            return result
        else:
            logger.warning("AI response for quantification check was not perfectly formatted or missing 'lacking_quantification' key.")
            logger.debug(f"RAW Quantification Check Response:\n{response.text if response else 'N/A'}")
            return {"lacking_quantification": [], "message": "Could not reliably analyze quantification due to AI response format."}
    except Exception as e:
        logger.error(f"AI Error (Quantify Impact): {e}", exc_info=True)
        return {"lacking_quantification": [], "message": f"Error during AI quantification check: {e}"}


def check_long_bullets_ai(resume_text, model):
    """Identifies long bullet points using AI and suggests shortening."""
    if not model: return {"long_bullets": [], "message": "AI model not available."}
    prompt = f"""
    Analyze the bullet points (lines typically starting with '*' or '-') in the following resume text.
    Identify bullet points that are excessively long (e.g., spanning more than 2 full lines of text or roughly 40+ words). Conciseness is key for resumes.
    For each long bullet point identified, provide the original text and suggest how to make it more concise OR split it into multiple, focused points.

    Return ONLY a valid JSON object in the following format:
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
        generation_config = {"temperature": 0.2}
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "long_bullets" in result:
            if not result["long_bullets"]:
                 return {"long_bullets": [], "message": "No overly long bullet points found."}
            logger.info(f"AI found {len(result['long_bullets'])} long bullet points.")
            return result
        else:
            logger.warning("AI response for long bullets check was not perfectly formatted or missing 'long_bullets' key.")
            logger.debug(f"RAW Long Bullets Check Response:\n{response.text if response else 'N/A'}")
            return {"long_bullets": [], "message": "Could not reliably analyze bullet length due to AI response format."}
    except Exception as e:
        logger.error(f"AI Error (Long Bullets): {e}", exc_info=True)
        return {"long_bullets": [], "message": f"Error during AI long bullet check: {e}"}


def check_active_voice_ai(resume_text, model):
    """Identifies passive voice using AI and suggests active voice alternatives."""
    if not model: return {"passive_sentences": [], "message": "AI model not available."}
    # --- UPDATED PROMPT ---
    prompt = f"""
    Act as an expert editor focused on resume writing. Analyze *all sentences* in the following resume text, particularly within the experience and project descriptions.
    Your primary goal is to identify *every instance* of passive voice. Passive voice uses forms of 'to be' (is, am, are, was, were) followed by a past participle (e.g., 'was managed', 'were completed'). Active voice is generally preferred in resumes (e.g., 'Managed X', 'Completed Y').
    For each passive sentence or phrase found, provide the original text and rewrite it in clear, impactful active voice, maintaining the original meaning.

    Return ONLY a valid JSON object in the following format:
    {{
      "passive_sentences": [
        {{
          "original": "<original passive voice sentence or phrase>",
          "active": "<rewritten active voice sentence or phrase>"
        }},
        ... // Include ALL instances found
      ]
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    # --- END UPDATED PROMPT ---
    try:
        generation_config = {"temperature": 0.1} # Low temp for factual analysis
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "passive_sentences" in result:
            if not result["passive_sentences"]:
                 return {"passive_sentences": [], "message": "Good use of active voice detected throughout."}
            logger.info(f"AI found {len(result['passive_sentences'])} potential passive voice instances.")
            return result
        else:
            logger.warning("AI response for active voice check was not perfectly formatted or missing 'passive_sentences' key.")
            logger.debug(f"RAW Active Voice Check Response:\n{response.text if response else 'N/A'}")
            return {"passive_sentences": [], "message": "Could not reliably analyze active voice due to AI response format."}
    except Exception as e:
        logger.error(f"AI Error (Active Voice): {e}", exc_info=True)
        return {"passive_sentences": [], "message": f"Error during AI active voice check: {e}"}


def check_hobbies_ai(resume_text, model):
    """Checks for a hobbies/interests section using AI and provides suggestions."""
    if not model: return {"found": False, "analysis": "AI model not available.", "suggestions": []}
    prompt = f"""
    Analyze the following resume text to determine if it includes a distinct section dedicated to hobbies, interests, volunteering, or similar personal activities outside of core work/education.

    1. State clearly whether such a section was found (true/false).
    2. If found, briefly comment on its relevance or presentation (1-2 sentences).
    3. If not found, suggest whether adding such a section could be beneficial (optional for many roles) and provide 3 diverse examples of interests suitable for a professional context (e.g., Mentoring, Photography, Open-source contributions, Marathon running, Volunteering for [Cause]).

    Return ONLY a valid JSON object in the following format:
    {{
      "found": <true_or_false>,
      "analysis": "<Brief analysis if found, or 'Section not found.' if not>",
      "suggestions": ["<suggestion 1>", "<suggestion 2>", ...] // Examples provided only if not found
    }}

    Resume Text:
    ```
    {resume_text}
    ```
    """
    try:
        generation_config = {"temperature": 0.3}
        response = model.generate_content(prompt, generation_config=generation_config)
        result = clean_and_parse_json(response.text)
        if result and "found" in result:
            if result["found"] and "suggestions" not in result: result["suggestions"] = []
            elif not result["found"] and "suggestions" not in result: result["suggestions"] = ["Consider adding an 'Interests' section if relevant to the roles you're applying for."]
            return result
        else:
             logger.warning("AI response for hobbies check was not perfectly formatted or missing 'found' key.")
             logger.debug(f"RAW Hobbies Check Response:\n{response.text if response else 'N/A'}")
             return {"found": False, "analysis": "Could not determine presence of hobbies section due to AI response format.", "suggestions": ["Consider adding an 'Interests' section if relevant."]}
    except Exception as e:
        logger.error(f"AI Error (Hobbies): {e}", exc_info=True)
        return {"found": False, "analysis": f"Error during AI hobbies check: {e}", "suggestions": []}


# --- Standard Check Functions (No Changes Needed) ---

def check_parse_rate(resume_text):
    """Simulates ATS parsing and returns a percentage."""
    total_chars = len(resume_text)
    if total_chars == 0: return 0
    non_whitespace_chars = len(re.findall(r'\S', resume_text))
    penalty = 0
    # Basic penalties for things that *might* hinder simple parsers
    if '\t' in resume_text: penalty += 5 # Tabs can cause alignment issues
    if re.search(r'\s{3,}', resume_text): penalty += 5 # Excessive spacing
    lines = resume_text.splitlines()
    lines_with_multiple_spaces_mid_line = sum(1 for line in lines if re.search(r'\S\s{3,}\S', line))
    if lines_with_multiple_spaces_mid_line > 3: penalty += 10 # Many lines with large gaps

    # Calculate base rate on non-whitespace density
    base_parse_rate = (non_whitespace_chars / total_chars) * 100 if total_chars > 0 else 0
    # Apply penalty and cap score
    final_parse_rate = max(0, round(base_parse_rate - penalty))
    return min(final_parse_rate, 99) # Cap below 100 as it's an estimate


def check_resume_length(resume_text):
    """Checks resume length (word count)."""
    word_count = len(resume_text.split())
    page_count_est = max(1, round(word_count / 450)) # Rough estimate: 450 words/page

    if word_count == 0: return "Resume is empty.", 0, 0
    elif word_count < 350:
        return f"Resume is likely too short ({word_count} words). Consider adding more detail, especially quantifiable achievements.", word_count, page_count_est
    elif word_count > 800 and page_count_est > 2 : # ~2 pages upper limit generally
        return f"Resume might be too long ({word_count} words, est. {page_count_est} pages). Aim for conciseness (1 page preferred, 2 max for extensive experience). Prioritize relevance.", word_count, page_count_est
    elif page_count_est == 2:
         return f"Resume length is {word_count} words (est. {page_count_est} pages). Ensure all content is highly relevant and impactful.", word_count, page_count_est
    else: # <= 1 page estimate
        return f"Resume length ({word_count} words, est. 1 page) is within the optimal range.", word_count, page_count_est


def check_buzzwords(resume_text):
    """Checks for common buzzwords/cliches."""
    buzzwords = [
        "results-driven", "team player", "detail-oriented", "go-getter", "synergy", "leverage",
        "proactive", "dynamic", "self-starter", "thought leader", "goal-oriented", "hardworking",
        "motivated", "passionate", "strategic thinker", "out-of-the-box", "think outside the box",
        "value add", "impactful", "excellent communication skills" # Added another common one
    ]
    found_buzzwords = []
    text_lower = resume_text.lower()
    for buzzword in buzzwords:
        # Use word boundaries to avoid matching parts of other words
        if re.search(r'\b' + re.escape(buzzword) + r'\b', text_lower):
            found_buzzwords.append(buzzword)
    return found_buzzwords


def check_contact_information(resume_text):
    """Checks for presence and format of contact information with improved regex."""
    contact_info = {}
    lines = resume_text.splitlines()
    text_lower = resume_text.lower()

    # --- Phone ---
    phone_pattern = r'(?:phone|mobile|tel\.?):?\s*([\+\(\)\d\s-]{10,})|(?:^|\s)([\+\(]?\d{1,3}[)-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    # Look for phone number, prioritizing keyword presence but allowing general patterns
    for line in lines[:5]: # Check near the top first
        match = re.search(phone_pattern, line, re.IGNORECASE)
        if match:
            # Group 1 is keyword match, Group 2 is general pattern
            phone_num = match.group(1) or match.group(2)
            if phone_num:
                 # Simple check to avoid matching sequences of numbers that aren't phone numbers (like IDs)
                 # Check if it contains typical phone chars and isn't excessively long/short
                 if len(re.findall(r'\d', phone_num)) >= 10 and len(re.findall(r'\d', phone_num)) <= 15:
                      contact_info['phone_number'] = phone_num.strip()
                      break # Found one near top

    # --- Email ---
    email_match = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', resume_text)
    if email_match:
        contact_info['email_address'] = email_match.group(0).strip()
        # Check for unprofessional domains
        unprofessional_domains = ["aol.com", "yahoo.com", "hotmail.com", "ymail.com"] # Added ymail
        if any(domain in contact_info['email_address'].lower() for domain in unprofessional_domains):
             contact_info['email_warning'] = "Consider using a more standard/professional email provider (e.g., Gmail, Outlook, custom domain)."

    # --- LinkedIn ---
    # Prioritize URL with /in/
    linkedin_match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[\w\-\.]+\/?', resume_text, re.IGNORECASE)
    if linkedin_match:
        contact_info['linkedin_url'] = linkedin_match.group(0).strip()

    # --- Portfolio/Website/GitHub ---
    # Look for GitHub specifically first
    github_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/[\w\-\.]+\/?', resume_text, re.IGNORECASE)
    if github_match:
        # Ensure it's not the same as LinkedIn if user has custom LI url matching github structure
        if 'linkedin_url' not in contact_info or github_match.group(0).strip() != contact_info['linkedin_url']:
             contact_info['github_url'] = github_match.group(0).strip()

    # Look for other URLs, avoiding LinkedIn and email domains
    portfolio_keywords = ['portfolio', 'website', 'blog', 'behance', 'dribbble', 'medium', 'gitlab'] # Added more
    url_pattern = r'(?:https?:\/\/)?(?:www\.)?[\w\-\.]+\.(?:com|io|dev|me|net|org|ai|co|tech|app|page)\/?[\w\-\/\.\?=&%]*' # Expanded TLDs and path chars
    potential_urls = re.findall(url_pattern, resume_text, re.IGNORECASE)

    found_portfolio = False
    for url in potential_urls:
        url_lower = url.lower()
        # Skip if already captured as LinkedIn, GitHub, or part of email
        if ('linkedin_url' in contact_info and contact_info['linkedin_url'] in url) or \
           ('github_url' in contact_info and contact_info['github_url'] in url) or \
           ('email_address' in contact_info and url_lower in contact_info['email_address']):
            continue

        # Check if it's near a keyword or looks like a plausible portfolio URL
        near_keyword = False
        for line in lines[:10]: # Check proximity in first few lines
             line_lower = line.lower()
             if url_lower in line_lower and any(keyword in line_lower for keyword in portfolio_keywords):
                  near_keyword = True
                  break

        # Accept if near keyword OR if it's a plausible domain (not just generic .com/.org)
        plausible_domain = any(tld in url_lower for tld in ['.dev', '.me', '.io', '.ai', '.tech', '.app', '.page', 'behance.net', 'dribbble.com', 'medium.com'])

        if near_keyword or plausible_domain:
            contact_info['portfolio_url'] = url.strip()
            found_portfolio = True
            break # Store the first plausible one

    # --- Location ---
    location_str = None
    # Look for keywords first
    for i, line in enumerate(lines[:10]): # Focus near top
        line_lower = line.lower()
        if 'address:' in line_lower or 'location:' in line_lower:
            location_part = re.split(r'address:|location:', line, flags=re.IGNORECASE)[-1].strip()
            if location_part:
                # Try to append next line if current one seems too short / likely just the keyword line
                if len(location_part) < 10 and i + 1 < len(lines) and len(lines[i+1].strip()) > 0 and ':' not in lines[i+1]:
                     location_str = lines[i+1].strip()
                else:
                    location_str = location_part
                break # Found based on keyword

    # If not found via keyword, try common patterns like City, State/Country near the top
    if not location_str:
         for line in lines[:5]: # Check near the top only
             # Pattern: Word(s), Word(s) OR just City/Country (less specific)
             loc_match = re.search(r'\b([A-Z][a-zA-Z\s\.-]+?)(?:,\s*([A-Z][a-zA-Z\s\.-]+))?\b', line)
             if loc_match:
                  potential_loc = loc_match.group(0).strip()
                  # Basic sanity checks - avoid all caps (likely section headers), too short, numeric IDs
                  if not potential_loc.isupper() and len(potential_loc) > 3 and not re.match(r'^\d+$', potential_loc):
                       # Avoid matching if it contains email/phone symbols unless it's long enough
                       if '@' not in potential_loc and 'http' not in potential_loc and '(' not in potential_loc:
                            location_str = potential_loc
                            break

    if location_str:
        # Final cleanup - remove potential noise if it looks very unlike a location
        location_str = location_str.strip(' .,')
        if len(re.findall(r'\d', location_str)) > 6 and len(location_str) < 25: # Too many digits for city/state/zip
             pass # Discard likely ID or code
        else:
             contact_info['location'] = location_str.strip()


    return contact_info


def check_essential_sections(resume_text):
    text_lower = resume_text.lower()
    sections_found = []
    # Use regex with word boundaries, potential variations, and line start assertion (^) for common titles
    if re.search(r'(?m)^\s*(skills?|technical skills?|proficiencies|technologies)\b', text_lower): sections_found.append("Skills")
    if re.search(r'(?m)^\s*(experience|work experience|professional experience|employment history|career)\b', text_lower): sections_found.append("Experience")
    if re.search(r'(?m)^\s*(education|academic background|qualifications)\b', text_lower): sections_found.append("Education")
    # Summary/Objective/Profile might not start the line but should be present
    if re.search(r'\b(summary|profile|objective|about me)\b', text_lower): sections_found.append("Summary/Profile/Objective")
    # Add check for Projects
    if re.search(r'(?m)^\s*(projects?|personal projects?|portfolio)\b', text_lower): sections_found.append("Projects")


    missing_sections = []
    # Ensure core sections are present by checking the found list
    if "Skills" not in sections_found: missing_sections.append("Skills/Technologies")
    if "Experience" not in sections_found: missing_sections.append("Experience")
    if "Education" not in sections_found: missing_sections.append("Education")
    # Allow either Summary OR Objective OR Profile
    if "Summary/Profile/Objective" not in sections_found: missing_sections.append("Summary/Profile/Objective")
    # Projects are often essential, especially for technical roles
    if "Projects" not in sections_found: missing_sections.append("Projects (Highly Recommended)")


    return sections_found, missing_sections


# --- Layout Analysis (Keep As Is) ---
def analyze_resume_layout(resume_file):
    layout_issues = []
    formatting_score = 100 # Start with perfect score
    try:
        resume_file.seek(0) # Ensure reading from the start
        pdf_reader = PyPDF2.PdfReader(resume_file)
        num_pages = len(pdf_reader.pages)

        # Page Count Check
        if num_pages == 0:
             logger.error("Could not read PDF pages.")
             return {"num_pages": 0, "layout_issues": ["Could not read PDF pages."], "formatting_score": 0}
        elif num_pages > 2:
            layout_issues.append(f"Resume is {num_pages} pages long. **Action:** Aim for 1-2 pages maximum for most roles. Prioritize relevance and conciseness.")
            formatting_score -= 20 # Heavier penalty for >2 pages
        elif num_pages == 2:
             layout_issues.append("Resume is 2 pages. **Action:** Ensure this length is necessary (e.g., 10+ years of relevant experience). Prioritize key information on page 1.")
             formatting_score -= 5

        full_text = ""
        try:
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text: full_text += page_text + "\n"
        except Exception as text_extract_error:
             layout_issues.append(f"Could not fully extract text for layout analysis: {text_extract_error}")
             formatting_score -= 10
             logger.warning(f"Text extraction failed during layout analysis: {text_extract_error}")

        # --- Content-Based Layout Checks (using extracted text) ---
        # These are heuristic checks and might have false positives/negatives

        # Font Consistency (Heuristic: Check for unusual characters/patterns - limited without font info)
        # This is very hard to check reliably from text alone. Placeholder suggestion.
        layout_issues.append("Font Usage: Ensure consistent use of 1-2 professional, readable fonts (e.g., Arial, Calibri, Georgia). Avoid script or overly decorative fonts.")
        # Cannot reliably penalize score for this from text alone.

        # Whitespace Check
        if re.search(r"\n\s*\n\s*\n", full_text): # More than one blank line
            layout_issues.append("Excessive vertical whitespace detected. **Action:** Remove extra blank lines between sections or paragraphs for better flow and space utilization.")
            formatting_score -= 5
        if re.search(r"[^\S\n]{3,}", full_text): # 3 or more spaces/tabs (not newlines)
             layout_issues.append("Avoid using multiple spaces/tabs for alignment. **Action:** Use standard indentation or section formatting.")
             formatting_score -= 5

        # Margins (Heuristic: Check line length consistency - very rough estimate)
        lines = full_text.splitlines()
        avg_line_length = sum(len(line.strip()) for line in lines if line.strip()) / len([line for line in lines if line.strip()]) if lines else 0
        if avg_line_length > 90: # Very long average lines might indicate narrow margins
            layout_issues.append("Lines seem long, possibly indicating narrow margins. **Action:** Ensure margins are adequate (0.5 - 1 inch recommended) for readability.")
            formatting_score -= 5
        elif avg_line_length < 40 and len(lines)>20: # Very short lines might indicate wide margins or columns
             layout_issues.append("Lines seem short, possibly indicating wide margins or use of columns. **Action:** Verify margins (0.5-1 inch). Avoid using columns if possible for ATS compatibility.")
             formatting_score -= 5
        else:
             layout_issues.append("Margins: Aim for standard margins (0.5-1 inch) for a balanced look.")
             # No penalty if average length seems reasonable

        # Complex Elements (Heuristic: Presence of unusual patterns - unreliable)
        # Cannot reliably detect tables, images, graphics from text. General advice:
        layout_issues.append("ATS Compatibility: Avoid complex tables, columns, images, headers/footers, text boxes, or graphics. Simple, single-column layouts parse best.")
        formatting_score -= 10 # Penalize slightly as a general caution

        # Final Score Calculation
        formatting_score = max(0, formatting_score) # Ensure score doesn't go below 0
        logger.info(f"Layout Analysis: {num_pages} pages, {len(layout_issues)} potential issues found. Score: {formatting_score}")
        return {"num_pages": num_pages, "layout_issues": layout_issues, "formatting_score": formatting_score}

    except PyPDF2.errors.PdfReadError as pdf_err:
        logger.error(f"Error reading PDF for layout analysis: {pdf_err}", exc_info=True)
        resume_file.seek(0) # Reset pointer
        return {"num_pages": "N/A", "layout_issues": ["Error reading PDF file. Ensure it's not corrupted or password-protected."], "formatting_score": 0}
    except Exception as e:
        logger.error(f"Error analyzing PDF layout: {str(e)}", exc_info=True)
        resume_file.seek(0) # Reset pointer
        return {"num_pages": "N/A", "layout_issues": [f"Error during layout analysis: {e}"], "formatting_score": 0}


# --- Main ATS Optimization Function ---
def get_ats_optimization_results(resume_text, resume_file, match_analysis=None, model=None):
    """Main function to perform all ATS optimization checks."""
    logger.info("Starting ATS Optimization process.")

    if not resume_text:
        logger.error("ATS Optimization cannot run: Resume text is empty.")
        st.error("Cannot perform ATS Optimization: Failed to extract text from resume.")
        return None # Return None if no text

    if not model:
         logger.error("Gemini AI model is not available for ATS checks.")
         st.error("Gemini AI model is not available. Cannot perform AI-driven checks.")
         # Still try to run standard checks if AI model fails
         ai_checks_results = {
             "spelling_grammar": {"errors": [], "message": "AI model unavailable."},
             "repetition": {"repeated_words": [], "message": "AI model unavailable."},
             "quantify_impact": {"lacking_quantification": [], "message": "AI model unavailable."},
             "long_bullets": {"long_bullets": [], "message": "AI model unavailable."},
             "active_voice": {"passive_sentences": [], "message": "AI model unavailable."},
             "hobbies": {"found": False, "analysis": "AI model unavailable.", "suggestions": []},
         }
         enhancements = {"message": "AI model unavailable for enhancement suggestions."}
    else:
        # --- Perform AI Checks ---
        logger.info("Running AI-powered ATS checks...")
        # Consider running these in parallel if possible, but sequential is simpler for now
        spelling_grammar_results = check_spelling_grammar_ai(resume_text, model)
        repetition_results = check_repetition_ai(resume_text, model)
        quantify_results = check_quantify_impact_ai(resume_text, model)
        long_bullet_results = check_long_bullets_ai(resume_text, model)
        active_voice_results = check_active_voice_ai(resume_text, model)
        hobbies_results = check_hobbies_ai(resume_text, model)
        logger.info("AI checks completed.")

        ai_checks_results = {
             "spelling_grammar": spelling_grammar_results if spelling_grammar_results else {"errors": [], "message": "Check failed or incomplete."},
             "repetition": repetition_results if repetition_results else {"repeated_words": [], "message": "Check failed or incomplete."},
             "quantify_impact": quantify_results if quantify_results else {"lacking_quantification": [], "message": "Check failed or incomplete."},
             "long_bullets": long_bullet_results if long_bullet_results else {"long_bullets": [], "message": "Check failed or incomplete."},
             "active_voice": active_voice_results if active_voice_results else {"passive_sentences": [], "message": "Check failed or incomplete."},
             "hobbies": hobbies_results if hobbies_results else {"found": False, "analysis": "Check failed or incomplete.", "suggestions": []},
        }

        # --- Run Enhancement Suggestions (uses AI) ---
        logger.info("Running AI enhancement suggestions...")
        enhancements = get_resume_enhancement_suggestions(model, resume_text, match_analysis)
        logger.info("Enhancement suggestions completed.")

    # --- Perform Standard Checks (Run regardless of AI model status) ---
    logger.info("Running standard ATS checks...")
    parse_rate = check_parse_rate(resume_text)
    length_feedback, word_count, page_count_est = check_resume_length(resume_text) # Get page estimate too
    buzzwords_found = check_buzzwords(resume_text)
    contact_info = check_contact_information(resume_text)
    essential_sections_found, essential_sections_missing = check_essential_sections(resume_text)
    logger.info("Standard checks completed.")

    # --- Perform Layout Analysis (Requires file object) ---
    layout_analysis_results = {"num_pages": page_count_est, "layout_issues": [], "formatting_score": 0} # Default using estimate
    if resume_file:
        logger.info("Running layout analysis on provided file...")
        layout_analysis_results = analyze_resume_layout(resume_file)
        logger.info("Layout analysis completed.")
    else:
        logger.warning("No resume file object provided for detailed layout analysis. Using estimates.")
        layout_analysis_results["layout_issues"].append("Could not perform detailed layout analysis (no file provided). Using estimate for page count.")
        # Try to estimate formatting score based on standard checks
        layout_analysis_results["formatting_score"] = 70 # Start lower if no file
        if 'Tabs or excessive spacing found' in length_feedback: layout_analysis_results["formatting_score"] -= 10
        if essential_sections_missing: layout_analysis_results["formatting_score"] -= 5 * len(essential_sections_missing)
        layout_analysis_results["formatting_score"] = max(0, layout_analysis_results["formatting_score"])


    # --- Combine Results ---
    results = {
        "ai_checks": ai_checks_results, # Contains results or 'unavailable' messages
        "standard_checks": {
            "parse_rate": parse_rate,
            "resume_length_feedback": length_feedback,
            "resume_word_count": word_count,
            "buzzwords": buzzwords_found,
            "contact_information": contact_info,
            "essential_sections_found": essential_sections_found,
            "essential_sections_missing": essential_sections_missing,
        },
        "layout_analysis": layout_analysis_results, # Contains detailed or estimated results
        "enhancement_suggestions": enhancements if enhancements else {"message": "Enhancement suggestions failed or were not generated."} # Provide default structure
    }
    logger.info("ATS Optimization results compiled.")

    # Log the structure of the contact info found for debugging
    logger.debug(f"Contact info check results: {contact_info}")

    return results

# --- End of ats_optimization.py ---