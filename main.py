# main.py (COMPLETE - Updated Cover Letter Display)

import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta # Ensure timedelta is imported
import json
import logging
import pandas as pd # Import pandas for DataFrame check

# --- Specific Google API Error Imports ---
try:
    from google.api_core.exceptions import NotFound, BadRequest, PermissionDenied, ResourceExhausted, InternalServerError, GoogleAPICallError
except ImportError:
    # Define dummy exceptions if google-api-core is not installed (less ideal)
    class GoogleAPICallError(Exception): pass
    class NotFound(GoogleAPICallError): pass
    class BadRequest(GoogleAPICallError): pass
    class PermissionDenied(GoogleAPICallError): pass
    class ResourceExhausted(GoogleAPICallError): pass
    class InternalServerError(GoogleAPICallError): pass
    logging.warning("google-api-core not found, using dummy exceptions for Google API errors.")


# --- Local Imports ---
from analysis import get_match_analysis
from utils import extract_text, clean_and_parse_json
from linkedin_optimization import generate_linkedin_optimization
from cover_letter import generate_custom_cover_letter
from interview_tips import generate_interview_tips
from career_roadmap import generate_career_roadmap
import job_recommendation
import ats_optimization

# --- Import Display Functions AND GLOBAL_CSS ---
from display import (
    GLOBAL_CSS, # Import the CSS constant
    display_match_results, display_linkedin_optimization, display_interview_tips,
    display_job_recommendation_and_roadmap, display_ats_optimization_results,
    display_career_roadmap, display_career_recommendation
)
# Import the function to fetch data *and* options
from dashboard import fetch_job_data_and_options, show_dashboard


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
TOOL_OPTIONS = {
    "Standard Analysis": "📊", "ATS Optimization": "🎯", "Cover Letter Synthesizer": "📨",
    "LinkedIn Optimization": "💼", "Interview Tips": "🤝", "Career Roadmap": "🗺️"
}
MODEL_OPTIONS = {
    "gemini-1.5-pro-latest": "Gemini 1.5 Pro (Latest)",
    "gemini-1.5-flash-latest": "Gemini 1.5 Flash (Latest)",
    "gemini-2.0-flash": "Gemini 2.0 Flash", # Re-added specific version
    "custom": "Enter Custom Model Name..."
}

# --- Error handling wrapper ---
def safe_analysis(func):
    """Wraps analysis functions to catch and display errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Analysis function {func.__name__} failed: {e}", exc_info=True)
            st.error(f"❌ Analysis failed unexpectedly: {str(e)}")
            if isinstance(e, (NotFound, BadRequest, PermissionDenied, GoogleAPICallError)):
                 st.caption(f"Details: Check API Key permissions, model name validity, or resource limits.")
            return None # Indicate failure
    return wrapper


# --- Helper functions ---
def show_analysis_progress():
    """Displays a simple progress simulation."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    stages = [("Initializing...", 0.1), ("Extracting Content...", 0.2), ("Analyzing Structure...", 0.4), ("Comparing Requirements...", 0.6), ("Generating Insights...", 0.8), ("Finalizing Results...", 1.0)]
    for stage, progress in stages:
        status_text.text(f"🔄 {stage}")
        progress_bar.progress(progress)
        time.sleep(0.3) # Simulate work
    progress_bar.empty()
    status_text.empty()

def init_session_state():
    """Initializes session state variables including defaults for filters."""
    defaults = {
        'dash_company': [], 'dash_title': [], 'dash_location': [],
        'dash_date': None, # Initialize date filter as None (no selection)
        'dash_status': "All",
        'jobs_df': None, # To store the main dataframe
        'filter_options': { # Default structure for options
             'companies': ['All'], 'positions': ['All'], 'cities': ['All'],
             'min_date': datetime.now().date() - timedelta(days=90),
             'max_date': datetime.now().date()
        },
        'selected_model_key_widget': list(MODEL_OPTIONS.keys())[2] # Default to third model (flash)
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    logging.info("Session state initialized/verified.")


# --- Main Application Logic ---
def main():
    st.set_page_config(
        page_title="Pathlight AI - Career Suite",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    init_session_state()

    # --- Fetch Data and Filter Options Early ---
    if st.session_state['jobs_df'] is None:
        logging.info("jobs_df not found in session_state. Fetching data and options...")
        with st.spinner("Loading market data..."):
            jobs_df, filter_options = fetch_job_data_and_options()
        if isinstance(jobs_df, pd.DataFrame) and not jobs_df.empty:
             st.session_state['jobs_df'] = jobs_df
             st.session_state['filter_options'] = filter_options
             logging.info(f"Data fetched ({len(jobs_df)} rows) and options stored.")
        elif isinstance(jobs_df, pd.DataFrame) and jobs_df.empty:
             logging.warning("fetch_job_data_and_options returned an empty DataFrame.")
             st.session_state['jobs_df'] = pd.DataFrame() # Store empty DF
             st.session_state['filter_options'] = filter_options # Keep options
             st.warning("No job data found in the source.")
        else:
             logging.error("fetch_job_data_and_options did not return a DataFrame.")
             st.error("Failed to load initial market data.")
             # Keep defaults
             jobs_df = st.session_state['jobs_df'] # Should be None or default empty
             filter_options = st.session_state['filter_options'] # Default
    else:
        jobs_df = st.session_state['jobs_df']
        filter_options = st.session_state['filter_options']
        logging.info("Using existing jobs_df and filter_options from session_state.")

    # --- Global Variables ---
    model = None
    resume_text = None
    job_description = None
    resume_file = None
    analysis_result = None
    final_model_name = ""

    # --- Sidebar ---
    with st.sidebar:
        st.markdown('<div class="sidebar-title"><h1><span style="color: #3498db;">Pathlight</span> AI</h1></div>', unsafe_allow_html=True)

        st.markdown("### 🛠️ Analysis Tools")
        tool_selection = st.radio("Select Analysis Type:", options=list(TOOL_OPTIONS.keys()), format_func=lambda x: f"{TOOL_OPTIONS[x]} {x}", help="Choose the analysis to perform.")
        st.divider()

        # --- Filters Section ---
        st.markdown("### 📊 Job Market Filters")
        st.markdown("<p class='filter-note'>Filters apply only to 'Job Market Insights'.</p>", unsafe_allow_html=True)

        min_date_option = filter_options.get('min_date', datetime.now().date() - timedelta(days=90))
        max_date_option = filter_options.get('max_date', datetime.now().date())

        st.date_input(
            "Date Range (Optional)",
            value=st.session_state.dash_date or (),
            min_value=min_date_option,
            max_value=max_date_option,
            key="dash_date_widget",
            help="Select a start and end date to filter job postings.",
            on_change=lambda: setattr(st.session_state, 'dash_date', st.session_state.dash_date_widget if isinstance(st.session_state.dash_date_widget, tuple) and len(st.session_state.dash_date_widget)==2 else None)
        )

        company_options = filter_options.get('companies', ['All'])
        st.multiselect(
            "Company", options=company_options, default=st.session_state.dash_company,
            key="dash_company_widget", help="Select one or more companies.",
            on_change=lambda: setattr(st.session_state, 'dash_company', st.session_state.dash_company_widget)
        )

        position_options = filter_options.get('positions', ['All'])
        st.multiselect(
            "Job Title", options=position_options, default=st.session_state.dash_title,
            key="dash_title_widget", help="Select one or more job titles.",
            on_change=lambda: setattr(st.session_state, 'dash_title', st.session_state.dash_title_widget)
        )

        city_options = filter_options.get('cities', ['All'])
        st.multiselect(
            "Location", options=city_options, default=st.session_state.dash_location,
            key="dash_location_widget", help="Select one or more locations.",
             on_change=lambda: setattr(st.session_state, 'dash_location', st.session_state.dash_location_widget)
        )

        st.radio(
            "Job Status", ["All", "Active", "Expired"],
            index=["All", "Active", "Expired"].index(st.session_state.dash_status),
            key="dash_status_widget",
            on_change=lambda: setattr(st.session_state, 'dash_status', st.session_state.dash_status_widget)
        )
        st.divider()

        # --- About Section ---
        st.markdown("""
            <div class='feature-card'>
                <h3>🔍 About Pathlight AI</h3>
                <small><i>Your AI career advancement assistant.</i></small>
                <ul>
                    <li><b>Resume Analysis:</b> AI insights, layout checks, cover letters, LinkedIn optimization, interview tips, career roadmaps.</li>
                    <li><b>AI Job Recommendations:</b> Personalized roles and actionable roadmaps.</li>
                    <li><b>Job Market Insights:</b> Real-time Indian job market dashboards.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # --- Main Content Area ---
    st.markdown(
        """
        <div class="main-title-box">
            <h1>Pathlight AI</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- AI Model Configuration ---
    with st.expander("⚙️ AI Model Configuration", expanded=False):
        st.markdown("#### Configure the Gemini AI Model")

        secret_api_key = st.secrets.get("GEMINI_API_KEY")
        has_secret_key = bool(secret_api_key)

        user_provided_key = st.text_input(
            "Leave blank to use the pre-configured key. Enter your own Gemini API key if needed.",
            type="password", value="", key="user_api_key_input",
            help="If provided, this key overrides any pre-configured one."
        )
        st.markdown("<small>Get an API Key from [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key)</small>", unsafe_allow_html=True)
        st.markdown("")

        potential_api_key = user_provided_key or secret_api_key
        key_source = "user" if user_provided_key else ("secret" if secret_api_key else "none")

        st.selectbox(
             "Select Gemini Model:", options=list(MODEL_OPTIONS.keys()),
             format_func=lambda x: MODEL_OPTIONS.get(x, x),
             help="'Flash' models are faster. 'Pro' models are more powerful.",
             key="selected_model_key_widget"
        )
        selected_model_key = st.session_state.selected_model_key_widget

        custom_model_name = ""; final_model_name = ""
        if selected_model_key == "custom":
            custom_model_name = st.text_input("Enter Custom Model Name:", placeholder="e.g., gemini-1.5-pro-latest", key="custom_model_input")
            final_model_name = custom_model_name.strip()
        else:
            final_model_name = selected_model_key

        model_status_placeholder = st.empty()
        model = None

        if potential_api_key and final_model_name:
            try:
                genai.configure(api_key=potential_api_key)
                model = genai.GenerativeModel(final_model_name)
                logging.info(f"Attempting to configure and test model '{final_model_name}'...")
                # Simple test call
                _ = model.generate_content("Hi", generation_config=genai.types.GenerationConfig(max_output_tokens=5, temperature=0.1, stop_sequences=["\n"]))
                logging.info(f"Model '{final_model_name}' test successful.")

                key_source_display = "provided" if key_source == "user" else "pre-configured"
                model_status_placeholder.success(f"✅ Configured: `{final_model_name}` using {key_source_display} API Key. Ready.")
                logging.info(f"Gemini Model configured: {final_model_name}. Source: {key_source_display}")

            except (NotFound, BadRequest, PermissionDenied, ResourceExhausted, InternalServerError, GoogleAPICallError) as google_err:
                 error_message = f"❌ Config Error (`{final_model_name}`): {google_err}"
                 logging.error(f"Google API Error during config/test: {google_err}", exc_info=False)
                 if isinstance(google_err, NotFound) or "is not found" in str(google_err) or "is not supported" in str(google_err): error_message += "\nModel unavailable/misnamed?"
                 elif key_source == "secret" and ("API key not valid" in str(google_err) or isinstance(google_err, PermissionDenied)): error_message += "\nPre-configured key invalid/lacks permissions?"
                 elif "API key not valid" in str(google_err) or isinstance(google_err, PermissionDenied): error_message += "\nPlease check the API Key provided."
                 model_status_placeholder.error(error_message)
                 model = None
            except Exception as e:
                error_message = f"❌ Unexpected Config Error (`{final_model_name}`): {e}."
                logging.error(f"Unexpected error during config/test: {e}", exc_info=True)
                if key_source == "secret": error_message += "\nTry providing your own key."
                model_status_placeholder.error(error_message)
                model = None
        elif not potential_api_key:
            model_status_placeholder.warning("⚠️ API Key required.")
        elif not final_model_name:
             if selected_model_key == "custom": model_status_placeholder.warning("⚠️ Enter custom model name.")
             else: model_status_placeholder.warning("⚠️ Select a model.")

    # --- TABS ---
    tab_resume, tab_jobs, tab_dashboard = st.tabs(["📄 Resume Analysis & Tools", "🎯 Job Recommendations", "📊 Job Market Insights"])

    # --- Resume Analysis & Tools Tab ---
    with tab_resume:
        st.markdown(
            """
            <div class="tab-title-box">
                <h2>Resume Analysis & Career Tools</h2>
            </div>
            <p class="tab-subtitle">
                Upload your resume and optionally paste a job description to leverage AI insights.
            </p>
            """,
            unsafe_allow_html=True
        )

        input_col1, input_col2 = st.columns([1, 1])
        with input_col1:
            st.markdown("##### 📄 Upload Resume")
            resume_file = st.file_uploader("Upload (PDF/DOCX)", type=['pdf', 'docx'], label_visibility="collapsed", key="resume_uploader_main")
            if resume_file:
                try:
                    resume_file.seek(0); resume_text = extract_text(resume_file); resume_file.seek(0)
                    if resume_text: st.success("✅ Resume text extracted.")
                    else: st.error("❌ Failed text extraction."); resume_text = None
                except Exception as e: st.error(f"❌ Error extracting: {e}"); resume_text = None
        with input_col2:
            st.markdown("##### 📝 Job Description (Optional)")
            job_description = st.text_area("Paste job description...", height=200, label_visibility="collapsed", key="job_desc_main")
            if job_description: st.success("✅ Job description provided.")
        st.markdown("---")

        analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
        with analyze_col2:
            is_model_ready = model is not None; is_resume_ready = resume_text is not None
            is_ats_ready = is_resume_ready and resume_file is not None and tool_selection == "ATS Optimization"
            is_tool_ready = is_resume_ready and (tool_selection != "ATS Optimization" or is_ats_ready)
            analyze_button = st.button(
                f"🚀 Run {tool_selection}", type="primary", use_container_width=True, key="analyze_button",
                disabled=not (is_model_ready and is_tool_ready)
            )
            if not is_model_ready: st.caption(":warning: Configure AI Model first.")
            elif not is_resume_ready: st.caption(":warning: Upload resume first.")
            elif tool_selection == "ATS Optimization" and not is_ats_ready: st.caption(":warning: ATS needs uploaded file.")

        if analyze_button:
            @safe_analysis
            def perform_analysis_local():
                 nonlocal analysis_result; logging.info(f"Running: {tool_selection}")
                 with st.spinner(f"Running {tool_selection}... Please wait."):
                    if tool_selection == "Standard Analysis":
                         if job_description and resume_text:
                            st.markdown("<div class='analysis-card'><h3>📊 Standard Analysis Results</h3></div>", unsafe_allow_html=True)
                            analysis_result = get_match_analysis(model, job_description, resume_text)
                            if analysis_result: display_match_results(analysis_result)
                         else: st.warning("⚠️ Standard Analysis requires both resume and job description.")

                    elif tool_selection == "ATS Optimization":
                         if resume_text and resume_file:
                            
                            match_analysis_for_ats = None
                            if job_description:
                                try:
                                    logging.info("Preliminary match analysis for ATS...")
                                    match_analysis_for_ats = get_match_analysis(model, job_description, resume_text)
                                except Exception as match_err: logging.warning(f"Preliminary match failed: {match_err}"); st.warning(f"Could not perform preliminary match: {match_err}")
                            resume_file.seek(0)
                            logging.info("Performing ATS optimization checks...")
                            analysis_result = ats_optimization.get_ats_optimization_results(resume_text, resume_file, match_analysis_for_ats, model)
                            if analysis_result: display_ats_optimization_results(analysis_result)
                         else: st.warning("⚠️ ATS Optimization requires an uploaded resume file.")

                    elif tool_selection == "Cover Letter Synthesizer":
                        if job_description and resume_text:
                            st.markdown("<div class='analysis-card'><h3>📨 Generated Cover Letter</h3></div>", unsafe_allow_html=True)
                            logging.info("Synthesizing cover letter...")
                            cover_letter = generate_custom_cover_letter(model, job_description, resume_text)
                            if cover_letter and not cover_letter.startswith("// Error"):
                                # --- DISPLAY COVER LETTER DIRECTLY ---
                                st.text_area("Cover Letter Output", cover_letter, height=400, label_visibility="collapsed", key="cover_letter_output")
                                st.download_button("⬇️ Download Cover Letter (.txt)", cover_letter, "cover_letter.txt", "text/plain")
                                # --- END DIRECT DISPLAY ---
                            elif cover_letter:
                                logging.error(f"Cover Letter generation failed (returned error message): {cover_letter}")
                                st.error(f"Could not generate cover letter: {cover_letter}")
                            else: # Handle None return
                                logging.error("Cover Letter generation failed (returned None).")
                                st.error("Failed to generate cover letter.")
                        else: st.warning("⚠️ Cover Letter requires resume and job description.")
                        analysis_result = None

                    elif tool_selection == "LinkedIn Optimization":
                         if resume_text:
                            
                            logging.info("Generating LinkedIn suggestions...")
                            analysis_result = generate_linkedin_optimization(model, resume_text)
                            if analysis_result: display_linkedin_optimization(analysis_result)
                         else: st.warning("⚠️ LinkedIn Optimization requires resume text.")

                    elif tool_selection == "Interview Tips":
                         if resume_text and job_description:
                            st.markdown("<div class='analysis-card'><h3>🤝 Interview Preparation Tips</h3></div>", unsafe_allow_html=True)
                            logging.info("Generating interview tips...")
                            analysis_result = generate_interview_tips(model, resume_text, job_description)
                            if analysis_result: display_interview_tips(analysis_result)
                         else: st.warning("⚠️ Interview Tips require resume and job description.")

                    elif tool_selection == "Career Roadmap":
                         if resume_text:
                    
                            logging.info("Generating career roadmap...")
                            analysis_result = generate_career_roadmap(model, resume_text)
                            if analysis_result:
                                if isinstance(analysis_result, dict):
                                    if "error" in analysis_result:
                                         logging.error(f"Roadmap fail: {analysis_result.get('error', 'Unknown')}"); st.error(f"Roadmap fail: {analysis_result.get('error', 'Unknown')}")
                                         st.code(analysis_result.get('raw_text', 'N/A'))
                                    else: display_career_roadmap(analysis_result)
                                elif isinstance(analysis_result, str): logging.warning("Roadmap simple text."); display_career_recommendation(analysis_result)
                                else: logging.error(f"Roadmap unexpected format: {type(analysis_result)}"); st.error("⚠️ Roadmap unexpected format.")
                         else: st.warning("⚠️ Career Roadmap requires resume text.")
                    else:
                         logging.error(f"Invalid tool selection: {tool_selection}"); st.error("Invalid tool selection.")
                         analysis_result = None
            perform_analysis_local()

    # --- Job Recommendations Tab ---
    with tab_jobs:
        st.markdown("<div class='analysis-card'><h3>🎯 AI Job Recommendation & Roadmap</h3><p class='neutral-feedback'>Get personalized job suggestions & roadmap.</p></div>", unsafe_allow_html=True)
        job_input_method = st.radio("Provide info via:", ["Paste Text", "Upload Resume"], horizontal=True, key="job_input_method")
        job_input_text = ""
        if job_input_method == "Paste Text": job_input_text = st.text_area("Describe skills, experience, goals...", height=250, key="job_text_input")
        else:
            job_resume_file = st.file_uploader("Upload resume (PDF/DOCX)", type=['pdf', 'docx'], key="job_resume_uploader")
            if job_resume_file:
                try:
                    job_resume_file.seek(0)
                    job_input_text = extract_text(job_resume_file)
                    job_resume_file.seek(0)
                    if job_input_text:
                        st.success("✅ Resume text extracted for recommendation!")
                    else: st.error("❌ Failed text extraction."); job_input_text = ""
                except Exception as e: st.error(f"Error extracting text: {e}"); job_input_text = ""

        job_rec_button = st.button("💡 Get Job Recommendation & Roadmap", key="job_recommend_button", type="primary", use_container_width=True, disabled=(model is None or not job_input_text))
        if model is None: st.caption(":warning: Configure AI Model first.")
        elif not job_input_text: st.caption(":warning: Provide input via text or resume.")
        if job_rec_button:
             if model and job_input_text:
                 logging.info("Generating job recommendation...")
                 with st.spinner("🧠 Generating recommendation..."):
                     try:
                        roadmap_result = job_recommendation.generate_job_recommendation_and_roadmap(model, job_input_text)
                        if roadmap_result and isinstance(roadmap_result, dict): display_job_recommendation_and_roadmap(roadmap_result)
                        elif roadmap_result: logging.error(f"Job Rec unexpected format: {type(roadmap_result)}"); st.error("Rec generation unexpected format."); st.write(roadmap_result)
                        else: logging.error("Failed job recommendation (None)."); st.error("Failed job recommendation.")
                     except Exception as e: logging.error(f"Error job rec generation: {e}", exc_info=True); st.error(f"Error during generation: {e}")

    # --- Job Market Insights Tab ---
    with tab_dashboard:
        try:
            logging.info("Showing dashboard tab.")
            show_dashboard()
        except Exception as e:
            logging.error(f"Failed dashboard tab load: {e}", exc_info=True)
            st.error(f"Failed to load dashboard: {e}")

    # --- Footer ---
    st.markdown("---")
    st.markdown("<p class='footer'>Created by <a href='https://www.linkedin.com/in/gagan-rao' target='_blank'>Gagan N</a> | Powered by Google Gemini</p>", unsafe_allow_html=True)

# --- Boilerplate ---
if __name__ == "__main__":
    main()