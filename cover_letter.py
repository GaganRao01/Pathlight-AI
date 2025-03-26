# cover_letter.py (Revised for Enhanced Personalization & Professionalism & Tone)

import streamlit as st
import re
import datetime # Import datetime to get today's date
from utils import clean_and_parse_json # Keep for potential future use

def generate_custom_cover_letter(model, job_description, resume_text):
    """
    Generates a highly personalized and professional cover letter by deeply
    integrating details from the job description and resume, aiming for a natural tone.
    """

    # --- Pre-extraction (Keep as Robust Fallbacks) ---
    applicant_name_match = re.search(r"^([A-Za-z\s'-]+)\n", resume_text)
    applicant_name_pre = applicant_name_match.group(1).strip() if applicant_name_match else "[Your Name]"
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
    email_pre = email_match.group(0) if email_match else "[Your Email]"
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
    phone_pre = phone_match.group(0) if phone_match else "[Your Phone Number]"
    linkedin_match = re.search(r'(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w-]+/?', resume_text, re.IGNORECASE)
    linkedin_pre = linkedin_match.group(0) if linkedin_match else "[Your LinkedIn Profile URL]"
    github_match = re.search(r'(https?:\/\/)?(www\.)?github\.com\/[\w-]+/?', resume_text, re.IGNORECASE)
    github_pre = github_match.group(0) if github_match else "[Your GitHub Profile URL]"
    company_name_pre = "[Company Name]" # Placeholder

    # Get today's date
    today_date = datetime.date.today().strftime("%B %d, %Y") # e.g., March 25, 2025

    # --- Enhanced Prompt ---
    prompt = f"""
Act as an expert career advisor and master cover letter writer. Your goal is to create an outstanding, highly personalized, and professional cover letter that sounds natural and human-written, significantly increasing the candidate's chances of getting an interview. Synthesize information *only* from the provided RESUME and JOB DESCRIPTION.

**CRITICAL INSTRUCTIONS:**

*   **TONE & VOICE:** Adopt a natural, engaging, and confident voice. Avoid overly formal, stiff, or robotic phrasing. The tone should be highly professional but also convey genuine enthusiasm and personality. Use smooth transitions between paragraphs and vary sentence structures.
*   **SUBTLE INTEGRATION:** Do NOT explicitly state "The job description requires..." or "My resume shows..." or "As highlighted in...". Instead, subtly weave the requirements and your relevant background together naturally within your sentences. *Show* the connection, don't just state it.
*   **DEEP PERSONALIZATION:** Every paragraph must connect the candidate's specific background (skills, achievements, experiences from the RESUME) to the specific requirements and context of the JOB DESCRIPTION and COMPANY in an authentic-sounding way.
*   **PROFESSIONALISM:** Maintain a confident, enthusiastic, and highly professional tone throughout. Avoid slang, casual language, and clichés (e.g., avoid "I am confident I possess the skills...").
*   **SHOW, DON'T TELL:** Instead of saying "I am skilled in X," demonstrate it by weaving in a specific achievement or experience from the resume where skill X was used effectively to achieve a result relevant to the job description. Use the STAR method implicitly *within a narrative*.
*   **QUANTIFY:** Naturally incorporate quantifiable achievements (numbers, percentages, scale) from the RESUME whenever possible to demonstrate impact.
*   **COMPANY FOCUS:** Show genuine, specific interest in *this* company. Reference details from the job description (e.g., company values, specific projects mentioned, required technologies, market position) and explain *why* they are exciting to *you*.
*   **CONCISENESS & IMPACT:** Be impactful yet concise. Aim for 3-5 sentences per paragraph. The entire letter should ideally fit on one page (approx. 250-400 words).
*   **STRUCTURE ADHERENCE:** Follow the exact structure below meticulously.

**COVER LETTER STRUCTURE:**

1.  **Header (Contact Information):**
    *   Applicant Info: Extract Applicant Full Name, Phone Number, Professional Email, LinkedIn URL, GitHub URL (if present) from the RESUME. Use fallbacks {applicant_name_pre}, {phone_pre}, {email_pre}, {linkedin_pre}, {github_pre} ONLY if extraction fails.
    *   Date: {today_date}
    *   Recipient Info: Extract Hiring Manager Name (default to "Hiring Manager"), Title (if known), Company Name (use fallback {company_name_pre} if needed), Company Address (if available) from the JOB DESCRIPTION.
    *   **Format:**
        [Your Full Name]
        [Your Phone Number] | [Your Email Address]
        [Your LinkedIn URL] | [Your GitHub URL (if applicable)]

        {today_date}

        [Hiring Manager Name (or "Hiring Manager")]
        [Hiring Manager Title (if known)]
        [Company Name]
        [Company Address (Optional, if available)]

2.  **Salutation:**
    *   Use "Dear Mr./Ms. [Last Name]," if name is found. If gender unclear, use "Dear [Full Name],".
    *   If name unknown, use "Dear Hiring Manager," or "Dear [Department, e.g., Engineering] Hiring Team,". ABSOLUTELY NO "To Whom It May Concern" or "Dear Sir/Madam".

3.  **Opening Paragraph (Introduction - Max 4 Sentences):**
    *   State the specific job title you are applying for.
    *   Immediately express genuine enthusiasm for *this specific role* at *this specific company*. Mention 1-2 compelling reasons based on the JOB DESCRIPTION (e.g., "I was excited to see the opening for [Job Title] because [Company Name]'s work in [Specific Area from JD] aligns perfectly with my passion for..." or "The opportunity to contribute to [Specific Project Mentioned in JD] at [Company Name] particularly caught my eye...").
    *   Naturally transition to a powerful sentence summarizing your most relevant qualification or achievement (from RESUME) that directly addresses a core requirement. Example: "...and I believe my proven ability to [Action Verb + Quantifiable Result from Resume, e.g., increase efficiency by 15%] in [Relevant Area] makes me a strong candidate."

4.  **Body Paragraph 1 (Skill/Experience Deep Dive - Max 5 Sentences):**
    *   Select the **top 1-2** most critical requirements/skills mentioned in the JOB DESCRIPTION.
    *   Weave in specific examples from your RESUME demonstrating proficiency using the STAR method implicitly *within a narrative structure*. Don't just list facts; tell a brief story.
    *   Example: "During my time at [Company from Resume], I encountered a challenge similar to [Requirement from JD]. By leveraging my expertise in [Skill 1 from Resume & JD] and implementing [Specific Action Taken], I was able to [Quantifiable Outcome from Resume, e.g., reduce processing time by 20%], an experience I'm eager to apply at [Company Name]."

5.  **Body Paragraph 2 (Company Alignment & Motivation - Max 5 Sentences):**
    *   Show you've researched the company beyond the job title. Reference specific aspects from the JD or well-known facts naturally (e.g., "I deeply admire [Company Name]'s commitment to [Value/Mission Mentioned in JD]..." or "The innovative approach [Company Name] takes towards [Project/Area Mentioned in JD] resonates strongly with...").
    *   Explain *why* these aspects attract you and how your values or career goals (as suggested by your RESUME experience) align.
    *   Connect how your background (from RESUME) can specifically contribute to *their* goals mentioned in the JD. Example: "My background in [Resume Skill/Area] aligns well with your goal of [Company Goal from JD], and I am confident I could quickly contribute to..."

6.  **(Optional) Body Paragraph 3 (Context/Unique Fit - Max 3 Sentences):**
    *   Use ONLY if needed to address another specific, crucial JD requirement (e.g., specific certification, language fluency) OR to briefly explain something unique from the resume (e.g., a major project, award) that strongly supports your candidacy. Keep it concise and integrated.

7.  **Closing Paragraph (Call to Action - Max 4 Sentences):**
    *   Briefly reiterate your strong interest and enthusiasm for the role.
    *   Connect your key strengths (e.g., [Key Area 1], [Key Area 2] from RESUME) to the *value you can bring* to [Company Name].
    *   Express proactive interest in discussing your fit further: "I am very interested in learning more about this opportunity and discussing how my skills in [Key Area 1] and [Key Area 2] can benefit [Company Name]. Thank you for your time and consideration."
    *   Subtly imply resume availability: "Further details on my qualifications and accomplishments are available for your review." (Avoid the blunt "My resume is attached.")

8.  **Sign-off:**
    *   Use "Sincerely," or "Best regards,".
    *   Follow with your full name (extracted or {applicant_name_pre}).

**Output:** Generate ONLY the cover letter text, starting with the header and ending after the final name. NO extra explanations, comments, or markdown formatting.

---
**Job Description:**
{job_description}
---
**Resume Text:**{resume_text}
---

**Generated Cover Letter:**
"""
    try:
        # Slightly higher temperature might allow for more natural phrasing, but keep it moderate
        generation_config = {"temperature": 0.6} # Adjusted from 0.65 maybe? Let's try 0.6
        response = model.generate_content(
            prompt,
            generation_config=generation_config
            )
        cleaned_response = response.text.strip().replace("```", "")

        # Check if it seems to start correctly (name or date) and contains common closing
        if (applicant_name_pre in cleaned_response[:200] or today_date in cleaned_response[:200]) and \
           ("Sincerely," in cleaned_response[-50:] or "Best regards," in cleaned_response[-50:]):
             return cleaned_response
        else:
             # Log the potentially problematic response for inspection
             print(f"--- POTENTIAL FORMAT ISSUE DETECTED (Cover Letter) ---")
             print(cleaned_response)
             print(f"--- END OF RESPONSE ---")
             st.warning("AI response might not be formatted correctly as a full cover letter. Displaying raw output.")
             return cleaned_response # Return raw text if format seems off

    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        # Log the prompt that caused the error if needed for debugging
        # print("--- PROMPT FAILED (Cover Letter) ---")
        # print(prompt)
        # print("--- END PROMPT ---")
        return f"// Error generating cover letter: {e} //"