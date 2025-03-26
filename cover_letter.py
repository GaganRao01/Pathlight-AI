# cover_letter.py (Revised for Enhanced Personalization & Professionalism)

import streamlit as st
import re
import datetime # Import datetime to get today's date
from utils import clean_and_parse_json # Keep for potential future use, though not strictly needed now

def generate_custom_cover_letter(model, job_description, resume_text):
    """
    Generates a highly personalized and professional cover letter by deeply
    integrating details from the job description and resume.
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
Act as an expert career advisor and master cover letter writer. Your goal is to create an outstanding, highly personalized, and professional cover letter that significantly increases the candidate's chances of getting an interview. Synthesize information *only* from the provided RESUME and JOB DESCRIPTION.

**CRITICAL INSTRUCTIONS:**

*   **DEEP PERSONALIZATION:** Do not write generic statements. Every paragraph must connect the candidate's specific background (skills, achievements, experiences from the RESUME) to the specific requirements and context of the JOB DESCRIPTION and COMPANY.
*   **PROFESSIONAL TONE:** Maintain a confident, enthusiastic, and highly professional tone throughout. Avoid slang, casual language, and clichés.
*   **SHOW, DON'T TELL:** Instead of saying "I am skilled in X," demonstrate it by citing a specific achievement or experience from the resume where skill X was used effectively to achieve a result relevant to the job description.
*   **QUANTIFY:** Incorporate quantifiable achievements (numbers, percentages, scale) from the RESUME whenever possible to demonstrate impact.
*   **COMPANY FOCUS:** Show genuine, specific interest in *this* company, referencing details from the job description (e.g., company values, specific projects mentioned, required technologies, market position).
*   **CONCISENESS:** Be impactful yet concise. Aim for 3-5 sentences per paragraph. The entire letter should ideally fit on one page (approx. 250-400 words).
*   **STRUCTURE ADHERENCE:** Follow the exact structure below meticulously.

**COVER LETTER STRUCTURE:**

1.  **Header (Contact Information):**
    *   **Applicant Info:** Extract Applicant Full Name, Phone Number, Professional Email, LinkedIn URL, GitHub URL (if present) from the RESUME. Use fallbacks ONLY if extraction fails.
        *   Fallbacks: Name: {applicant_name_pre}, Phone: {phone_pre}, Email: {email_pre}, LinkedIn: {linkedin_pre}, GitHub: {github_pre}
    *   **Date:** Use today's date: {today_date}
    *   **Recipient Info:** Extract Hiring Manager Name (default to "Hiring Manager"), Title (if known), Company Name, Company Address (if available) from the JOB DESCRIPTION.
        *   Fallback Company: {company_name_pre}
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
    *   Use "Dear Mr./Ms. [Last Name]," if name is found. If gender is unclear, use "Dear [Full Name],".
    *   If name unknown, use "Dear Hiring Manager," or "Dear [Department, e.g., Engineering] Hiring Team,". ABSOLUTELY NO "To Whom It May Concern" or "Dear Sir/Madam".

3.  **Opening Paragraph (Introduction - Max 4 Sentences):**
    *   Clearly state the specific job title you are applying for (from JOB DESCRIPTION).
    *   Express strong, specific enthusiasm for *this role* at *this company*. Mention 1-2 compelling reasons based on the JOB DESCRIPTION (e.g., alignment with company's mission in [Area], opportunity to use [Key Skill from JD] on [Specific Project Mentioned], admiration for their work in [Specific Field]).
    *   Immediately follow with a powerful sentence summarizing your most relevant qualification or achievement (from RESUME) that directly addresses a core requirement in the JOB DESCRIPTION. Example: "My proven ability to [Action Verb + Quantifiable Result from Resume, e.g., increase efficiency by 15%] in [Relevant Area] aligns directly with your need for [Requirement from JD]."

4.  **Body Paragraph 1 (Skill/Experience Deep Dive - Max 5 Sentences):**
    *   Select the **top 2** most critical requirements/skills mentioned in the JOB DESCRIPTION.
    *   For each requirement, provide a specific example from your RESUME demonstrating your proficiency. Use the STAR method implicitly: Describe the Situation/Task briefly, detail the Action you took (using resume keywords/verbs), and highlight the quantifiable Result.
    *   Example: "In my previous role at [Company from Resume], I was tasked with [Task related to JD requirement]. Leveraging my expertise in [Skill 1 from Resume & JD] and [Skill 2 from Resume & JD], I [Specific Action Taken], which resulted in [Quantifiable Outcome from Resume, e.g., a 20% reduction in processing time]."

5.  **Body Paragraph 2 (Company Alignment & Motivation - Max 5 Sentences):**
    *   Demonstrate you've researched the company beyond the job title. Reference specific aspects mentioned in the JOB DESCRIPTION or widely known facts (e.g., "I am particularly drawn to [Company Name]'s commitment to [Value/Mission Mentioned in JD]..." or "Your recent work in [Project/Area Mentioned in JD] resonates strongly with my passion for...").
    *   Explain *why* these aspects attract you and how your own values or career goals (evident from your RESUME) align with the company's direction.
    *   Connect how your skills/experience (from RESUME) can specifically contribute to *their* goals or mission mentioned in the JD. Example: "My experience in [Resume Skill/Area] would enable me to directly contribute to your goal of [Company Goal from JD]."

6.  **(Optional) Body Paragraph 3 (Context/Unique Fit - Max 3 Sentences):**
    *   Use ONLY if needed to address a specific JD requirement not covered (e.g., specific certification, language fluency mentioned in JD and Resume) OR to briefly explain something unique from the resume (e.g., a relevant major project, a specific award). Keep it concise.

7.  **Closing Paragraph (Call to Action - Max 4 Sentences):**
    *   Briefly reiterate your strong interest in the role and confidence in your fit.
    *   Mention 1-2 key skills/experiences (from RESUME) again in the context of how they will benefit the company.
    *   Politely state your desire for an interview: "I am eager to discuss how my qualifications in [Key Area 1] and [Key Area 2] can contribute to [Company Name]'s success. Thank you for your time and consideration."
    *   Refer the reader to your attached resume. "My resume, attached for your review, provides further detail on my background."

8.  **Sign-off:**
    *   Use "Sincerely," or "Best regards,".
    *   Follow with your full name (extracted from resume or fallback).

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
        # generation_config = {"temperature": 0.65, "max_output_tokens": 1200} # Slightly more creative, enough length
        response = model.generate_content(
            prompt,
            # generation_config=generation_config
            )
        # Basic cleaning
        cleaned_response = response.text.strip().replace("```", "")

        # Check if it seems to start correctly (name or date)
        # More lenient check: does it contain likely header elements near the start?
        if applicant_name_pre in cleaned_response[:200] or today_date in cleaned_response[:200] or "Dear" in cleaned_response[:300]:
             return cleaned_response
        else:
             st.warning("AI response might not be formatted correctly as a cover letter. Displaying raw output.")
             print(f"RAW AI RESPONSE:\n{response.text.strip()}") # Log raw response for debugging
             return response.text.strip()

    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        # Optionally log the prompt that caused the error
        # print("--- PROMPT FAILED ---")
        # print(prompt)
        # print("--- END PROMPT ---")
        return f"// Error generating cover letter: {e} //"