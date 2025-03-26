# display.py (COMPLETE - Updated with Roadmap Separators)

import streamlit as st
import json
import re

# --- CSS Definition (Includes roadmap separator style) ---
# This is applied ONCE in main.py now.
GLOBAL_CSS = """
    <style>
    /* --- General --- */
    .main > div { padding: 1rem 2rem; max-width: 1300px; margin: 0 auto; }
    .theme-aware-text { color: var(--text-color, inherit) !important; }
    .positive-feedback { color: #2ecc71; font-weight: bold; }
    .negative-feedback { color: #e74c3c; font-weight: bold; }
    .neutral-feedback { color: var(--text-color, #555); font-style: italic; font-size: 0.95em;}
    .highlight-buzzword { background-color: rgba(241, 196, 15, 0.2); padding: 0.1em 0.3em; border-radius: 3px; font-weight: bold; color: #f39c12; }
    .section-heading { color: #3498db !important; font-size: 1.4rem; font-weight: bold; margin-bottom: 1.5rem; text-align: left; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
    .subsection-heading { color: #5dade2 !important; font-size: 1.15rem; font-weight: bold; margin-top: 1.5rem; margin-bottom: 0.8rem; text-align: left; }
    .category-title { /* Used inside tabs/sections */ color: #3498db !important; font-size: 1.25rem; font-weight: bold; margin-bottom: 1rem; text-align: left; }
    /* Reduce gap between Streamlit's vertical blocks */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] { gap: 0.8rem !important; }
    .footer { text-align: center; padding: 15px; margin-top: 30px; font-size: 0.9em; color: #888; width: 100%; }

    /* --- Buttons --- */
    .stButton>button { height: 3rem; font-size: 1.1rem; transition: transform 0.2s; border-radius: 8px; }
    .stButton>button:hover { transform: translateY(-2px); }

    /* --- Cards --- */
    .analysis-card { background: rgba(100, 149, 237, 0.05); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(100, 149, 237, 0.2); margin-bottom: 1rem; }
    .feature-card { background: rgba(100, 149, 237, 0.05); padding: 1rem; border-radius: 8px; border: 1px solid rgba(100, 149, 237, 0.2); transition: transform 0.2s; margin-bottom: 1rem; }
    .suggestion-card, .suggestion-card-red, .suggestion-card-green { background-color: var(--secondary-background-color, #f8f9fa); padding: 1rem; border-radius: 8px; margin-bottom: 0.8rem; color: var(--text-color, #000000); border: 1px solid rgba(0, 0, 0, 0.05); box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
    [data-theme="dark"] .suggestion-card,
    [data-theme="dark"] .suggestion-card-red,
    [data-theme="dark"] .suggestion-card-green { background-color: var(--secondary-background-color, #2f3136); border: 1px solid rgba(255,255,255,0.08); }

    .suggestion-card { border-left: 4px solid #3498db; }
    .suggestion-card-red { border-left: 4px solid #e74c3c; }
    .suggestion-card-green { border-left: 4px solid #2ecc71; }
    .suggestion-card p { margin-bottom: 0.5rem; }
    .suggestion-card p:last-child { margin-bottom: 0; }
    .list-item { padding: 0.7rem; margin-bottom: 0.5rem; border-radius: 5px; background: var(--secondary-background-color, #f8f9fa); color: var(--text-color, #000000); border: 1px solid rgba(0, 0, 0, 0.1); }
    [data-theme="dark"] .list-item { background: var(--secondary-background-color, #2f3136); border: 1px solid rgba(255,255,255,0.08); }
    /* Score card styles (Used in Standard Analysis) */
    .score-card { background: linear-gradient(135deg, #1e3799 0%, #0c2461 100%); padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    .score-card h1, .score-card p, .score-card h3, .score-card h2 { color: white !important; margin: 0; padding: 0; }
    .metric-card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); padding: 1rem; border-radius: 10px; margin: 0.5rem; text-align: center; }
    .metric-card h3, .metric-card h2, .metric-card p { text-align: center; margin: 0; padding: 0; color: white !important; }


    /* --- ATS Specific & Reused Styles --- */
    .ats-section-card { background: linear-gradient(135deg, #1e3799 0%, #0c2461 100%); padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
    .ats-section-card h4 { color: white !important; font-size: 1.3rem; font-weight: bold; margin: 0; text-align: left; }
    .ats-check-container { background: var(--secondary-background-color, #f0f2f6); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; border: 1px solid rgba(0, 0, 0, 0.08); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); }
    [data-theme="dark"] .ats-check-container { background: var(--secondary-background-color, #262730); border: 1px solid rgba(255, 255, 255, 0.1); }
    .ats-check-container:empty { display: none !important; padding: 0 !important; margin: 0 !important; border: none !important; box-shadow: none !important; }
    .ats-check-title { color: #3498db !important; font-size: 1.15rem; font-weight: bold; margin-bottom: 1rem; padding-bottom: 0.3rem; border-bottom: 2px solid #3498db; text-align: left; }
    .ats-metric-row { display: flex; flex-wrap: wrap; justify-content: space-around; gap: 1rem; margin-bottom: 1rem; }
    .ats-metric-item { background: var(--background-color, #ffffff); padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid rgba(0, 0, 0, 0.1); flex: 1; min-width: 150px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 0.5rem; }
    [data-theme="dark"] .ats-metric-item { background: var(--secondary-background-color, #2f3136); border: 1px solid rgba(255,255,255,0.08); }
    .ats-metric-item h5 { color: #3498db !important; font-size: 0.9rem; margin-bottom: 0.5rem; font-weight: bold; text-transform: uppercase; }
    .ats-metric-item p { color: var(--text-color, #000000) !important; font-size: 1.8rem; font-weight: bold; margin: 0; }
    .ats-metric-item small { display: block; font-size: 0.85em; color: var(--text-color, #555); margin-top: 0.5rem; line-height: 1.3; }
    .correction-block { margin-bottom: 1rem; padding: 0.8rem; border-radius: 5px; background: rgba(231, 76, 60, 0.05); border: 1px solid rgba(231, 76, 60, 0.2); }
    .correction-block .original { color: #e74c3c; text-decoration: line-through; display: block; margin-bottom: 0.3rem; }
    .correction-block .corrected { color: #2ecc71; font-weight: bold; display: block; margin-bottom: 0.3rem; }
    .correction-block .explanation { font-size: 0.9em; color: var(--text-color, #555); font-style: italic; display: block; }
    .repetition-item { margin-bottom: 1rem; padding: 0.8rem; border-radius: 5px; background: rgba(243, 156, 18, 0.05); border: 1px solid rgba(243, 156, 18, 0.2); }
    .repetition-item .word { font-weight: bold; color: #f39c12; }
    .repetition-item .suggestions { font-size: 0.95em; margin-top: 0.3rem; }

    /* --- Roadmap Specific Styles --- */
    .roadmap-container { margin-bottom: 1.5rem; }
    .roadmap-timeline-title { color: #3498db !important; font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; padding-bottom: 0.3rem; border-bottom: 1px solid #eee; }
    [data-theme="dark"] .roadmap-timeline-title { border-bottom: 1px solid #444; }

    .roadmap-goal-item {
        background: var(--secondary-background-color, #f8f9fa);
        padding: 1rem 1.5rem;
        border-radius: 0; /* Remove individual border radius */
        margin-bottom: 0; /* Remove margin */
        border: 1px solid rgba(0,0,0,0.05);
        border-bottom: none; /* No bottom border on the item itself */
    }
    .roadmap-goal-item:first-of-type { border-radius: 8px 8px 0 0; } /* Top corners for the first item */
    .roadmap-goal-item:last-of-type {
        border-radius: 0 0 8px 8px; /* Bottom corners for the last item */
        border-bottom: 1px solid rgba(0,0,0,0.05); /* Add bottom border only to the last */
        margin-bottom: 1rem; /* Add margin after the last item in a list */
    }
    [data-theme="dark"] .roadmap-goal-item {
        background: var(--secondary-background-color, #2f3136);
        border-color: rgba(255,255,255,0.08);
    }
     [data-theme="dark"] .roadmap-goal-item:last-of-type {
        border-bottom-color: rgba(255,255,255,0.08);
     }

    /* Custom HR style for Roadmap */
    hr.roadmap-separator {
        border: none; /* Remove default HR border */
        height: 1px; /* Set height */
        background-color: rgba(0, 0, 0, 0.1); /* Set separator color */
        margin: 0; /* Reset margin */
    }
    [data-theme="dark"] hr.roadmap-separator {
         background-color: rgba(255, 255, 255, 0.1); /* Dark theme color */
    }

    .roadmap-goal-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;}
    .roadmap-goal-title span { font-size: 1.3em; line-height: 1; }
    .roadmap-goal-description { font-size: 0.95em; margin-bottom: 0.7rem; line-height: 1.5; }
    .roadmap-goal-resources h6 { font-size: 0.9em; font-weight: bold; margin-bottom: 0.3rem; color: #5dade2;}
    .roadmap-goal-resources ul { list-style-type: none; padding-left: 0; margin-bottom: 0; }
    .roadmap-goal-resources li { font-size: 0.9em; margin-bottom: 0.2rem; }
    .skills-category { margin-bottom: 1rem; }
    .skills-category h6 { font-weight: bold; color: #5dade2; margin-bottom: 0.5rem;}
    .skills-category ul { list-style-position: inside; padding-left: 0.5rem; margin-bottom: 0.5rem;}
    .skills-category li { margin-bottom: 0.3rem; }

    /* --- Expander Styling --- */
    .stExpander {
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
        background-color: var(--background-color);
    }
    [data-theme="dark"] .stExpander {
         border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stExpander header {
        font-weight: bold;
        font-size: 1.05em;
        color: #3498db;
    }
    .stExpander div[data-testid="stExpanderDetails"] > div {
         background-color: transparent !important;
         padding-top: 0.5rem;
    }
    .stExpander .streamlit-expanderContent {
        padding: 0 1rem 1rem 1rem;
    }
        /* --- Title Styling --- */
    .main-title-gradient {
        background: -webkit-linear-gradient(45deg, #5dade2, #a569bd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 2.8rem;
        margin: 0; padding: 0;
    }
    .tab-title-styled { color: #5dade2; font-weight: bold; margin-bottom: 0.2rem; }
    .tab-subtitle-styled { color: #888; font-style: italic; margin-top: 0; }

    /* --- Box Styles for Titles --- */
    .main-title-box {
        background: linear-gradient(135deg, #2c3e50 0%, #1e3799 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }
    .main-title-box h1 {
        margin: 0; padding: 0; font-size: 3.2rem; font-weight: bold;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
        color: white !important; background: none;
        -webkit-background-clip: unset; -webkit-text-fill-color: unset;
    }
    .tab-title-box {
        background-color: #5dade2; color: white;
        padding: 1rem 1.5rem; border-radius: 10px;
        text-align: center; margin-bottom: 0.8rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .tab-title-box h2 { margin: 0; padding: 0; font-size: 1.8rem; font-weight: bold; color: white !important; }
    .tab-subtitle {
        color: var(--text-color, #555); font-style: italic;
        text-align: center; margin-bottom: 1.5rem; font-size: 1.0em;
    }
    </style>
    """

# --- display_match_results ---
def display_match_results(analysis):
    """Displays the standard resume vs. job description match analysis."""
    if not analysis or not isinstance(analysis, dict):
        st.error("Invalid analysis data received for display.")
        return

    overall_score = analysis.get('overall_match', 'N/A')
    keyword_score = analysis.get('keyword_match_score', 'N/A')
    semantic_score = analysis.get('semantic_similarity_score', 'N/A')
    impact_data = analysis.get('impact_scoring', {})
    achievement_score = impact_data.get('achievement_metrics', 'N/A')

    st.markdown(f"""
        <div class="score-card">
            <h1 style='font-size: 72px; margin: 0; line-height: 1.2;'>{overall_score if isinstance(overall_score, (int, float)) else 'N/A'}%</h1>
            <p style='font-size: 24px; margin: 10px 0;'>Overall Match (Hybrid)</p>
            <div style='display: flex; justify-content: center; flex-wrap: wrap; gap: 20px; margin-top: 20px;'>
                <div class="metric-card">
                    <h3 style='margin-bottom: 5px;'>Keyword Match</h3>
                    <h2>{keyword_score if isinstance(keyword_score, (int, float)) else 'N/A'}%</h2>
                </div>
                <div class="metric-card">
                    <h3 style='margin-bottom: 5px;'>Semantic Similarity</h3>
                    <h2>{semantic_score if isinstance(semantic_score, (int, float)) else 'N/A'}%</h2>
                </div>
                <div class="metric-card">
                    <h3 style='margin-bottom: 5px;'>Impact Score (Est.)</h3>
                    <h2>{achievement_score if isinstance(achievement_score, (int, float)) else 'N/A'}%</h2>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<h3 class="section-heading">🔑 Key Terms from Job Description</h3>', unsafe_allow_html=True)
    keywords = analysis.get('keywords_from_job_description', [])
    if keywords and isinstance(keywords, list):
        keyword_str = ", ".join([f"`{k}`" for k in keywords])
        st.markdown(f'<div class="list-item">{keyword_str}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="suggestion-card neutral-feedback">No specific keywords extracted.</div>', unsafe_allow_html=True)

    st.markdown('<h3 class="section-heading" style="margin-top: 2rem;">📊 Category Match Scores</h3>', unsafe_allow_html=True)
    category_data_main = analysis.get('categories', {})
    categories = ['technical_skills', 'soft_skills', 'experience', 'education']
    cols = st.columns(len(categories))
    for i, category in enumerate(categories):
         with cols[i]:
            cat_name = category.replace('_', ' ').title()
            category_data = category_data_main.get(category, {})
            match = category_data.get('match', 0)
            match_display = f"{match}%" if isinstance(match, (int, float)) else "N/A"
            st.markdown(f"""
                <div class="metric-card theme-aware-text" style="background: rgba(52, 152, 219, 0.1); height: 100%; border-radius: 8px;">
                    <h4 class="category-title" style="font-size: 1.1rem; margin-bottom: 0.5rem;">{cat_name}</h4>
                    <h2 class="stat-counter" style="color: #3498db; font-size: 2.5rem;">{match_display}</h2>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('<h3 class="section-heading" style="margin-top: 2rem;">📋 Detailed Analysis</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["Technical Skills", "Soft Skills", "Experience", "Education", "ATS Summary", "Impact Analysis"])

    with tabs[0]: # Technical Skills
        st.markdown('<h4 class="category-title">Technical Skills Analysis</h4>', unsafe_allow_html=True)
        category_data = category_data_main.get('technical_skills', {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<h5 class="subsection-heading">Present Skills</h5>', unsafe_allow_html=True)
            present_skills = category_data.get('present_skills', [])
            if present_skills:
                 for skill in present_skills: st.markdown(f'<div class="list-item">✅ {skill}</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="list-item neutral-feedback">No specific matching technical skills found.</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<h5 class="subsection-heading">Missing Skills</h5>', unsafe_allow_html=True)
            missing_skills = category_data.get('missing_skills', [])
            if missing_skills:
                for missing_skill in missing_skills:
                    skill_name = missing_skill.get('skill', 'Unknown Skill')
                    with st.expander(f"⚠️ {skill_name}"):
                        st.markdown(f"**Reason:** {missing_skill.get('reason', 'N/A')}")
                        recs = missing_skill.get('remediation_suggestions', [])
                        if recs:
                            st.markdown("**Recommendations:**")
                            for s in recs: st.markdown(f"- {s}")
                        res = missing_skill.get('resource_links', [])
                        if res:
                            st.markdown("**Resources:**")
                            for r in res:
                                title = r.get('title', 'Link'); url = r.get('url','#')
                                if url and url != "#": st.markdown(f'- [{title}]({url})', unsafe_allow_html=True)
                                else: st.markdown(f"- {title} (Link N/A)")
            else: st.markdown('<div class="list-item positive-feedback">No significant missing technical skills identified.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Improvement Suggestions</h5>', unsafe_allow_html=True)
        imps = category_data.get('improvement_suggestions', [])
        if imps:
             for s in imps: st.markdown(f'<div class="suggestion-card">💡 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">No general technical skill suggestions.</div>', unsafe_allow_html=True)

    with tabs[1]: # Soft Skills
        st.markdown('<h4 class="category-title">Soft Skills Analysis</h4>', unsafe_allow_html=True)
        category_data = category_data_main.get('soft_skills', {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<h5 class="subsection-heading">Present Skills (Inferred)</h5>', unsafe_allow_html=True)
            present_skills = category_data.get('present_skills', [])
            if present_skills:
                 for skill in present_skills: st.markdown(f'<div class="list-item">✅ {skill}</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="list-item neutral-feedback">Ensure experience demonstrates skills implicitly.</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<h5 class="subsection-heading">Missing Skills (from JD)</h5>', unsafe_allow_html=True)
            missing_skills = category_data.get('missing_skills', [])
            if missing_skills:
                for missing_skill in missing_skills:
                     skill_name = missing_skill.get('skill', 'Unknown Skill')
                     with st.expander(f"⚠️ {skill_name}"):
                         st.markdown(f"**Reason:** {missing_skill.get('reason', 'N/A')}")
                         recs = missing_skill.get('remediation_suggestions', [])
                         if recs:
                             st.markdown("**Recommendations:**")
                             for s in recs: st.markdown(f"- {s}")
            else: st.markdown('<div class="list-item positive-feedback">No significant missing soft skills identified.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Improvement Suggestions</h5>', unsafe_allow_html=True)
        imps = category_data.get('improvement_suggestions', [])
        if imps:
             for s in imps: st.markdown(f'<div class="suggestion-card">💡 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">No general soft skill suggestions.</div>', unsafe_allow_html=True)

    with tabs[2]: # Experience
        st.markdown('<h4 class="category-title">Experience Analysis</h4>', unsafe_allow_html=True)
        category_data = category_data_main.get('experience', {})
        st.markdown('<h5 class="subsection-heading">Strengths</h5>', unsafe_allow_html=True)
        strengths = category_data.get('strengths', [])
        if strengths:
             for s in strengths: st.markdown(f'<div class="list-item">✅ {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="list-item neutral-feedback">Highlight achievements aligning with job needs.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Gaps</h5>', unsafe_allow_html=True)
        gaps = category_data.get('gaps', [])
        if gaps:
            for gap_info in gaps:
                gap_name = gap_info.get('gap', 'Potential Gap')
                with st.expander(f"⚠️ {gap_name}"):
                    st.markdown(f"**Reason:** {gap_info.get('reason', 'N/A')}")
                    recs = gap_info.get('remediation_suggestions', [])
                    if recs:
                        st.markdown("**Recommendations:**")
                        for s in recs: st.markdown(f"- {s}")
        else: st.markdown('<div class="list-item positive-feedback">No significant experience gaps identified.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Improvement Suggestions</h5>', unsafe_allow_html=True)
        imps = category_data.get('improvement_suggestions', [])
        if imps:
             for s in imps: st.markdown(f'<div class="suggestion-card">💡 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">Focus on tailoring bullet points.</div>', unsafe_allow_html=True)

    with tabs[3]: # Education
        st.markdown('<h4 class="category-title">Education Analysis</h4>', unsafe_allow_html=True)
        category_data = category_data_main.get('education', {})
        st.markdown('<h5 class="subsection-heading">Relevant Qualifications</h5>', unsafe_allow_html=True)
        quals = category_data.get('relevant_qualifications', [])
        if quals:
             for q in quals: st.markdown(f'<div class="list-item">✅ {q}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="list-item neutral-feedback">Ensure education listed clearly.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Gaps</h5>', unsafe_allow_html=True)
        gaps = category_data.get('gaps', [])
        if gaps:
            for gap in gaps:
                 gap_name = gap.get('gap', 'Potential Gap')
                 with st.expander(f"⚠️ {gap_name}"):
                    st.markdown(f"**Reason:** {gap.get('reason', 'N/A')}")
                    recs = gap.get('remediation_suggestions', [])
                    if recs:
                        st.markdown("**Recommendations:**")
                        for s in recs: st.markdown(f"- {s}")
                    res = gap.get('resource_links', [])
                    if res:
                        st.markdown("**Resources:**")
                        for r in res:
                            title = r.get('title', 'Link'); url = r.get('url','#')
                            if url and url != "#": st.markdown(f'- [{title}]({url})', unsafe_allow_html=True)
                            else: st.markdown(f"- {title} (Link N/A)")
        else: st.markdown('<div class="list-item positive-feedback">No significant education gaps found.</div>', unsafe_allow_html=True)
        st.markdown('<h5 class="subsection-heading">Improvement Suggestions</h5>', unsafe_allow_html=True)
        imps = category_data.get('improvement_suggestions', [])
        if imps:
             for s in imps: st.markdown(f'<div class="suggestion-card">💡 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">No general education suggestions.</div>', unsafe_allow_html=True)

    with tabs[4]: # ATS Summary
        st.markdown('<h4 class="category-title">ATS Optimization Summary (Preview)</h4>', unsafe_allow_html=True)
        st.markdown('<div class="suggestion-card neutral-feedback">Run "ATS Optimization" tool for full breakdown.</div>', unsafe_allow_html=True)
        ats_summary = analysis.get('ats_optimization', {})
        if ats_summary:
             kw_suggestions = ats_summary.get('keyword_optimization', [])
             fmt_issues = ats_summary.get('formatting_issues', [])
             sec_improvements = ats_summary.get('section_improvements', [])
             preview_suggestions = kw_suggestions[:1] + fmt_issues[:1] + sec_improvements[:1]
             if preview_suggestions:
                  st.markdown('<h5 class="subsection-heading">Suggestions Snippet</h5>', unsafe_allow_html=True)
                  valid_suggestions = [s for s in preview_suggestions if s]
                  if valid_suggestions:
                       for suggestion in valid_suggestions:
                            st.markdown(f'<div class="suggestion-card">💡 {suggestion}</div>', unsafe_allow_html=True)
                  else:
                       st.markdown('<div class="suggestion-card positive-feedback">✅ Basic ATS checks seem okay based on preview.</div>', unsafe_allow_html=True)
             else: st.markdown('<div class="suggestion-card positive-feedback">✅ Basic ATS checks seem okay based on preview.</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">No ATS summary provided.</div>', unsafe_allow_html=True)

    with tabs[5]: # Impact Analysis
        st.markdown('<h4 class="category-title">Impact Analysis (Resume Content)</h4>', unsafe_allow_html=True)
        impact_data = analysis.get('impact_scoring', {})
        ach_met = impact_data.get("achievement_metrics", "N/A")
        act_vrb = impact_data.get("action_verbs", "N/A")
        qua_res = impact_data.get("quantifiable_results", "N/A")

        st.markdown('<div class="ats-metric-row">', unsafe_allow_html=True)
        st.markdown(f'<div class="ats-metric-item"><h5>Achievement Metrics</h5><p>{ach_met if isinstance(ach_met, (int, float)) else "N/A"}%</p><small>Highlighting achievements.</small></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ats-metric-item"><h5>Action Verbs Usage</h5><p>{act_vrb if isinstance(act_vrb, (int, float)) else "N/A"}%</p><small>Use of strong action verbs.</small></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ats-metric-item"><h5>Quantifiable Results</h5><p>{qua_res if isinstance(qua_res, (int, float)) else "N/A"}%</p><small>Inclusion of numbers, %, $.</small></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Impact Improvement Suggestions</h5>', unsafe_allow_html=True)
        imps = impact_data.get('improvement_suggestions', [])
        if imps:
             for s in imps: st.markdown(f'<div class="suggestion-card">📈 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">Focus on action verbs & quantifying results.</div>', unsafe_allow_html=True)


# --- display_enhancement_suggestions ---
def display_enhancement_suggestions(enhancements):
    """Displays detailed resume enhancement suggestions. Called by ATS display."""
    if not enhancements or not isinstance(enhancements, dict):
        st.warning("No enhancement suggestions data available.")
        return
    try:
        st.markdown('<h5 class="subsection-heading">Professional Summary</h5>', unsafe_allow_html=True)
        summary_section = enhancements.get("summary_section", {})
        if summary_section.get("has_summary", False):
            st.markdown('<div class="suggestion-card-green">✅ Includes professional summary.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="suggestion-card-red">⚠️ Missing professional summary.</div>', unsafe_allow_html=True)
        with st.expander("View Summary Suggestions & Example"):
            sample_summary = summary_section.get('sample_summary')
            if sample_summary:
                st.markdown("<h6>Suggested Summary Example:</h6>", unsafe_allow_html=True); st.info(f"{sample_summary}")
            else: st.markdown("<p class='neutral-feedback'>No example summary provided.</p>", unsafe_allow_html=True)
            st.markdown("<h6>Improvement Points:</h6>", unsafe_allow_html=True)
            sugs = summary_section.get("suggestions", [])
            if sugs:
                 for s in sugs: st.markdown(f"- {s}")
            else: st.markdown("<p class='neutral-feedback'>No specific points provided.</p>", unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Bullet Points Analysis</h5>', unsafe_allow_html=True)
        bullet_points_section = enhancements.get("bullet_points", {})
        strength = bullet_points_section.get("strength", "N/A")
        st.markdown(f"**Overall Bullet Point Strength (Est.):** `{strength if isinstance(strength, (int, float)) else 'N/A'}%`")
        with st.expander("View Bullet Point Improvements"):
            weak_bullets = bullet_points_section.get("weak_bullets", [])
            if weak_bullets:
                st.markdown("<h6>Weak Bullets & Suggestions:</h6>", unsafe_allow_html=True)
                for bp in weak_bullets:
                    original = bp.get('original','N/A'); improved = bp.get('improved','N/A'); reason = bp.get('reason', 'N/A')
                    st.markdown(f"""<div class="correction-block"><span class="original">**Original:** {original}</span><span class="corrected">**Improved:** {improved}</span><span class="explanation">**Reason:** {reason}</span></div>""", unsafe_allow_html=True)
            else: st.markdown('<div class="suggestion-card-green">No specific weak bullets identified.</div>', unsafe_allow_html=True)
            st.markdown("<h6>General Bullet Point Suggestions:</h6>", unsafe_allow_html=True)
            gen_sugs = bullet_points_section.get("general_suggestions",[])
            if gen_sugs:
                 for s in gen_sugs: st.markdown(f"- {s}")
            else: st.markdown("<p class='neutral-feedback'>Focus on STAR method and quantification.</p>", unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Action Verbs Enhancement</h5>', unsafe_allow_html=True)
        power_verbs_section = enhancements.get("power_verbs", {})
        with st.expander("View Action Verb Suggestions"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Current Verbs (Examples):**")
                cur_v = power_verbs_section.get("current_verbs", [])
                if cur_v: st.markdown("\n".join([f"- `{v}`" for v in cur_v[:15]]))
                else: st.markdown("N/A")
            with col2:
                st.markdown("**Suggested Stronger Alternatives:**")
                sug_v = power_verbs_section.get("suggested_verbs", [])
                if sug_v: st.markdown("\n".join([f"- `{v}`" for v in sug_v[:15]]))
                else: st.markdown("N/A")
            explanation = power_verbs_section.get('explanation', 'Use varied, strong action verbs.')
            st.markdown(f"**Explanation:** *{explanation}*")

        st.markdown('<h5 class="subsection-heading">Keyword Analysis</h5>', unsafe_allow_html=True)
        keywords_section = enhancements.get("keywords", {})
        with st.expander("View Keyword Suggestions"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Present Keywords (Examples):**"); pres_k = keywords_section.get("present_keywords", [])
                if pres_k: st.info(f"`{', '.join(pres_k[:30])}`")
                else: st.markdown("N/A")
            with col2:
                st.markdown("**Missing Keywords (Consider Adding):**"); miss_k = keywords_section.get("missing_keywords", [])
                if miss_k: st.warning(f"`{', '.join(miss_k[:30])}`")
                else: st.markdown("None specifically identified.")
            st.markdown("<h6>General Suggestions:</h6>", unsafe_allow_html=True)
            key_sugs = keywords_section.get("suggestions", [])
            if key_sugs:
                 for s in key_sugs: st.markdown(f"- {s}")
            else: st.markdown("<p class='neutral-feedback'>Integrate relevant job keywords naturally.</p>", unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Technical Profile Enhancement</h5>', unsafe_allow_html=True)
        tech_profile_section = enhancements.get("technical_profile", {})
        with st.expander("View Technical Profile Suggestions"):
            st.markdown("<h6>Technologies to Consider Adding/Highlighting:</h6>", unsafe_allow_html=True)
            tech_add = tech_profile_section.get("technologies_to_add", [])
            if tech_add: st.markdown("\n".join([f"- `{t}`" for t in tech_add]))
            else: st.markdown("<p class='neutral-feedback'>Review skills based on target jobs.</p>", unsafe_allow_html=True)
            st.markdown("<h6>Recommended Certifications (Optional):</h6>", unsafe_allow_html=True)
            certs = tech_profile_section.get("certifications", [])
            if certs:
                for cert in certs:
                    name = cert.get('certification_name', 'N/A'); url = cert.get('url'); rel = cert.get('relevance', 'N/A')
                    if url and url != "#": st.markdown(f"- [{name}]({url}): {rel}", unsafe_allow_html=True)
                    else: st.markdown(f"- **{name}**: {rel}")
            else: st.markdown("<p class='neutral-feedback'>No specific certifications recommended.</p>", unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Soft Skills Enhancement</h5>', unsafe_allow_html=True)
        soft_skills_section = enhancements.get("soft_skills", {})
        with st.expander("View Soft Skills Enhancement"):
            st.markdown("<h6>Soft Skills to Consider Highlighting:</h6>", unsafe_allow_html=True)
            soft_add = soft_skills_section.get("soft_skills_to_add", [])
            if soft_add: st.markdown("\n".join([f"- `{s}`" for s in soft_add]))
            else: st.markdown("<p class='neutral-feedback'>Demonstrate soft skills via experience bullets.</p>", unsafe_allow_html=True)
            st.markdown("<h6>General Suggestions:</h6>", unsafe_allow_html=True)
            soft_sugs = soft_skills_section.get("soft_skills_improvement_suggestions", [])
            if soft_sugs:
                 for s in soft_sugs: st.markdown(f"- {s}")
            else: st.markdown("<p class='neutral-feedback'>Weave soft skills into descriptions.</p>", unsafe_allow_html=True)

        st.markdown('<h5 class="subsection-heading">Overall Resume Suggestions</h5>', unsafe_allow_html=True)
        overall_suggestions = enhancements.get("overall_suggestions", [])
        if overall_suggestions:
             for s in overall_suggestions: st.markdown(f'<div class="suggestion-card">💡 {s}</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="suggestion-card neutral-feedback">Ensure clarity and consistency.</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error displaying enhancement suggestions: {str(e)}")
        st.exception(e)


# --- display_linkedin_optimization ---
def display_linkedin_optimization(linkedin_suggestions):
    """Displays LinkedIn optimization suggestions with improved UI using expanders."""
    if not linkedin_suggestions or not isinstance(linkedin_suggestions, dict):
        st.error("Unable to generate LinkedIn optimization suggestions or data invalid.")
        return

    try:
        st.markdown('<div class="ats-section-card"><h4><span style="font-size: 1.5em;">💼</span> LinkedIn Profile Optimization</h4></div>', unsafe_allow_html=True)
        st.markdown("<p class='neutral-feedback' style='margin-bottom: 1.5rem;'>Actionable suggestions to enhance your LinkedIn presence based on your resume.</p>", unsafe_allow_html=True)

        if headline_suggs := linkedin_suggestions.get("headline_suggestions"):
            with st.expander("✨ Headline Suggestions", expanded=True):
                st.markdown("Craft a compelling, keyword-rich headline. Examples:")
                for i, item in enumerate(headline_suggs):
                    st.markdown(f"**Example {i+1}:** `{item.get('headline', 'N/A')}`")
                    st.markdown(f"<small><i>Rationale: {item.get('rationale', 'N/A')}</i></small>", unsafe_allow_html=True)
                    if i < len(headline_suggs) - 1: st.markdown("---")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No specific headline suggestions.</div>', unsafe_allow_html=True)

        if about_suggs := linkedin_suggestions.get("about_section_suggestions"):
            with st.expander("📝 About Section (Summary)"):
                 st.markdown("Suggestions to make your 'About' section more engaging:")
                 for i, item in enumerate(about_suggs):
                     focus = item.get('type', 'General'); suggestion = item.get('suggestion', 'N/A'); ref = item.get('resume_reference')
                     st.markdown(f"**Focus:** {focus}"); st.markdown(f"**Suggestion:** {suggestion}")
                     if ref: st.markdown(f"<small><i>(Relates to: {ref})</i></small>", unsafe_allow_html=True)
                     if i < len(about_suggs) - 1: st.markdown("---")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No specific "About" suggestions.</div>', unsafe_allow_html=True)

        if exp_suggs := linkedin_suggestions.get("experience_section_suggestions"):
            with st.expander("🛠️ Experience Section"):
                st.markdown("Enhance experience descriptions:")
                for i, item in enumerate(exp_suggs):
                     role_company = item.get('job_title_company', 'N/A'); suggestions = item.get('suggestions', []); ref = item.get('resume_reference')
                     st.markdown(f"**For Role:** `{role_company}`")
                     if suggestions:
                          st.markdown("Suggestions:")
                          for s in suggestions: st.markdown(f"- {s}")
                     if ref: st.markdown(f"<small><i>(Relates to: {ref})</i></small>", unsafe_allow_html=True)
                     if i < len(exp_suggs) - 1: st.markdown("---")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No specific "Experience" suggestions.</div>', unsafe_allow_html=True)

        if skills_suggs := linkedin_suggestions.get("skills_section_suggestions"):
             with st.expander("💡 Skills & Endorsements"):
                 skills_add = skills_suggs.get("skills_to_add", []); skills_prio = skills_suggs.get("skills_to_prioritize_endorsements", []); endorsement_strategy = skills_suggs.get('endorsement_strategy')
                 if skills_add: st.markdown("**Skills to Add/Ensure Listed (from Resume):**"); st.markdown(f"`{', '.join(skills_add)}`")
                 if skills_prio: st.markdown("**Prioritize Endorsements For:**"); st.markdown(f"`{', '.join(skills_prio)}`")
                 if endorsement_strategy: st.markdown("**Endorsement Strategy:**"); st.markdown(f"{endorsement_strategy}")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No specific "Skills" suggestions.</div>', unsafe_allow_html=True)

        if edu_suggs := linkedin_suggestions.get('education_section_suggestions'):
             with st.expander("🎓 Education Section"):
                 st.markdown("Suggestions:")
                 for s in edu_suggs: st.markdown(f"- {s}")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No specific "Education" suggestions.</div>', unsafe_allow_html=True)

        if add_suggs := linkedin_suggestions.get("additional_sections_suggestions"):
             with st.expander("➕ Additional Sections (Projects, Certs, etc.)"):
                 st.markdown("Consider adding/enhancing these sections:")
                 for i, item in enumerate(add_suggs):
                     section = item.get('section_name', 'N/A'); suggestion = item.get('suggestion', 'N/A'); ref = item.get('resume_reference')
                     st.markdown(f"**Section:** {section}"); st.markdown(f"**Suggestion:** {suggestion}")
                     if ref: st.markdown(f"<small><i>(Relates to: {ref})</i></small>", unsafe_allow_html=True)
                     if i < len(add_suggs) - 1: st.markdown("---")
        else: st.markdown('<div class="suggestion-card neutral-feedback">No suggestions for additional sections.</div>', unsafe_allow_html=True)

        if overall_tips := linkedin_suggestions.get('overall_profile_tips'):
             with st.expander("🚀 Overall Profile Tips"):
                 st.markdown("General tips:")
                 for tip in overall_tips: st.markdown(f"- {tip}")

    except Exception as e:
        st.error(f"Error displaying LinkedIn optimization: {str(e)}")
        st.exception(e)


# --- display_interview_tips ---
def display_interview_tips(interview_tips):
    """Displays personalized interview tips with improved UI."""
    if not interview_tips or not isinstance(interview_tips, dict):
        st.error("Unable to generate interview preparation tips or data invalid.")
        return
    try:
        st.markdown('<div class="ats-section-card"><h4><span style="font-size: 1.5em;">🤝</span> Interview Preparation Tips</h4></div>', unsafe_allow_html=True)
        st.markdown("<p class='neutral-feedback' style='margin-bottom: 1.5rem;'>Tailored advice for this specific role, based on your resume and the job description.</p>", unsafe_allow_html=True)

        if focus_areas := interview_tips.get("preparation_focus_areas"):
             with st.expander("⭐ Key Preparation Focus Areas", expanded=True):
                  for i, item in enumerate(focus_areas):
                      st.markdown(f"**🎯 Focus:** {item.get('area', 'N/A')}")
                      st.markdown(f"**Action:** {item.get('action', 'N/A')}")
                      if i < len(focus_areas) - 1: st.markdown("---")

        if deep_dive := interview_tips.get("resume_deep_dive_prompts"):
            with st.expander("📄 Resume Deep Dive: Be Ready For...", expanded=True):
                 st.markdown("Interviewers may ask for more detail on:")
                 for i, item in enumerate(deep_dive):
                     st.markdown(f"**Potential Prompt:** \"{item.get('prompt', 'N/A')}\"")
                     st.markdown(f"**Your Strategy:** {item.get('advice', 'N/A')}")
                     if ref := item.get('resume_reference'): st.markdown(f"<small><i>(Refers to: {ref})</i></small>", unsafe_allow_html=True)
                     if i < len(deep_dive) - 1: st.markdown("---")

        if behavioral_qs := interview_tips.get("potential_behavioral_questions"):
             with st.expander("💬 Potential Behavioral Questions (Use STAR)"):
                  st.markdown("Prepare STAR-based answers using specific resume examples:")
                  for i, item in enumerate(behavioral_qs):
                       st.markdown(f"**Question:** \"{item.get('question', 'N/A')}\"")
                       if source := item.get('resume_example_source'): st.markdown(f"<small><i>Consider examples from: {source}</i></small>", unsafe_allow_html=True)
                       if star := item.get('suggested_star_points'):
                           st.markdown(f"  - **S (Situation):** {star.get('Situation','...')}")
                           st.markdown(f"  - **T (Task):** {star.get('Task','...')}")
                           st.markdown(f"  - **A (Action):** {star.get('Action','...')}")
                           st.markdown(f"  - **R (Result):** {star.get('Result','...')}")
                       if i < len(behavioral_qs) - 1: st.markdown("---")

        if technical_qs := interview_tips.get("potential_technical_questions"):
             with st.expander("💻 Potential Role-Specific / Technical Questions"):
                  st.markdown("Be ready to discuss technical aspects:")
                  for i, item in enumerate(technical_qs):
                       st.markdown(f"**Question:** \"{item.get('question', 'N/A')}\"")
                       st.markdown(f"**Response Strategy:** {item.get('advice', 'N/A')}")
                       if ref := item.get('resume_reference'): st.markdown(f"<small><i>(Relates to: {ref})</i></small>", unsafe_allow_html=True)
                       if i < len(technical_qs) - 1: st.markdown("---")

        if ask_qs := interview_tips.get("questions_candidate_should_ask"):
             with st.expander("❓ Insightful Questions to Ask Them"):
                  st.markdown("Asking thoughtful questions shows engagement:")
                  for i, item in enumerate(ask_qs):
                       st.markdown(f"**Question:** \"{item.get('question', 'N/A')}\"")
                       st.markdown(f"<small><i>Purpose: {item.get('purpose', 'N/A')}</i></small>", unsafe_allow_html=True)
                       if i < len(ask_qs) - 1: st.markdown("---")

    except Exception as e:
        st.error(f"Error displaying interview tips: {str(e)}")
        st.exception(e)


# --- display_career_recommendation ---
def display_career_recommendation(recommendation_text):
    """Displays simple text recommendation/roadmap with basic styling."""
    try:
        st.markdown('<div class="ats-section-card"><h4>🗺️ Career Recommendation</h4></div>', unsafe_allow_html=True)
        formatted_text = recommendation_text.replace('\n\n', '<br><br>').replace('\n', '<br>')
        formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_text)
        formatted_text = re.sub(r'(?m)^### (.*?)(<br>|$)', r'<h5>\1</h5>', formatted_text)
        formatted_text = re.sub(r'(?m)^#### (.*?)(<br>|$)', r'<h6>\1</h6>', formatted_text)
        formatted_text = re.sub(r'(?m)^[\*\-]\s*(.*?)(?=<br>|$)', r'<li>\1</li>', formatted_text)
        formatted_text = re.sub(r'(<li>.*?</li>\s*(?:<br>)?)+', r'<ul>\g<0></ul>', formatted_text, flags=re.DOTALL)
        formatted_text = formatted_text.replace('<ul><br>', '<ul>').replace('<br></ul>', '</ul>').replace('<ul></ul>', '')
        st.markdown(f'<div class="ats-check-container">{formatted_text}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying simple career recommendation text: {e}")
        st.text(recommendation_text)

# --- End of Chunk 1/2 ---
# display.py (COMPLETE - Part 2/2)

# --- display_job_recommendation_and_roadmap ---
def display_job_recommendation_and_roadmap(result):
    """Displays the combined job role and roadmap."""
    if not result or not isinstance(result, dict):
        st.error("No job recommendation data received or data is invalid.")
        return

    try:
        st.markdown('<h3 class="section-heading">🎯 Job Recommendation & Roadmap</h3>', unsafe_allow_html=True)

        with st.expander("Recommended Role & Justification", expanded=True):
             rec_role = result.get('recommended_role', 'N/A')
             justification = result.get('justification', 'No justification provided.')
             st.markdown(f"**Recommended Job Role:** `{rec_role}`")
             st.markdown("**Justification:**")
             st.markdown(f"<div class='suggestion-card'>{justification}</div>", unsafe_allow_html=True)

        roadmap_data = result.get("roadmap", {})
        if roadmap_data:
            with st.expander("Detailed Career Roadmap", expanded=True):
                timeline_tabs = st.tabs(["➡️ Short Term", "⏳ Mid Term", "🚀 Long Term"])
                timeframes = ["short_term", "mid_term", "long_term"]

                for i, timeframe in enumerate(timeframes):
                     with timeline_tabs[i]:
                          goals = roadmap_data.get(timeframe, [])
                          if goals:
                              goal_count = len(goals)
                              for idx, goal in enumerate(goals):
                                  st.markdown('<div class="roadmap-goal-item">', unsafe_allow_html=True)
                                  icon = goal.get('icon', '🎯' if timeframe == "short_term" else ('⏳' if timeframe == "mid_term" else '🚀'))
                                  title = goal.get('title', 'Goal')
                                  st.markdown(f'<div class="roadmap-goal-title"><span>{icon}</span> {title}</div>', unsafe_allow_html=True)
                                  st.markdown(f'<div class="roadmap-goal-description">{goal.get("description", "N/A")}</div>', unsafe_allow_html=True)

                                  if resources := goal.get("resources"):
                                      st.markdown('<div class="roadmap-goal-resources"><h6>Resources:</h6><ul>', unsafe_allow_html=True)
                                      for res in resources:
                                          res_title = res.get('title', '[Resource]')
                                          if res_url := res.get('url'):
                                              if res_url != "#": st.markdown(f'<li><a href="{res_url}" target="_blank">{res_title}</a></li>', unsafe_allow_html=True)
                                              else: st.markdown(f'<li>{res_title}</li>', unsafe_allow_html=True) # Display title if URL is #
                                          else: st.markdown(f'<li>{res_title}</li>', unsafe_allow_html=True) # Display title if URL is missing
                                      st.markdown('</ul></div>', unsafe_allow_html=True)
                                  st.markdown('</div>', unsafe_allow_html=True) # end roadmap-goal-item
                                  # Add HR separator if not the last item
                                  if idx < goal_count - 1:
                                      st.markdown('<hr class="roadmap-separator">', unsafe_allow_html=True)
                          else:
                              st.markdown(f'<p class="neutral-feedback">No specific goals outlined for {timeframe.replace("_", " ")}.</p>', unsafe_allow_html=True)

                # --- Skills and Technologies ---
                if skills_tech := roadmap_data.get("skills_technologies"):
                    st.markdown('<h5 class="subsection-heading">Key Skills and Technologies to Develop</h5>', unsafe_allow_html=True)
                    num_cols = min(len(skills_tech), 3)
                    cols = st.columns(num_cols) if num_cols > 0 else [st]
                    for idx, area in enumerate(skills_tech):
                        with cols[idx % num_cols]:
                            skill_area_title = area.get('skill_area','Skill Area')
                            st.markdown(f"<div class='skills-category'><h6>{skill_area_title}</h6>", unsafe_allow_html=True)
                            if skills := area.get("skills"):
                                 st.markdown("<ul>" + "".join([f"<li>{skill}</li>" for skill in skills]) + "</ul>", unsafe_allow_html=True)
                            else: st.markdown("<ul><li>N/A</li></ul>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                else:
                     st.markdown('<p class="neutral-feedback">No specific skills breakdown provided in roadmap.</p>', unsafe_allow_html=True)
        else:
            st.warning("Roadmap details (timeline, skills) not found in the result.")

        # --- Certifications ---
        if certifications := result.get("certifications"):
             with st.expander("Recommended Certifications"):
                 cert_count = len(certifications)
                 for idx, cert in enumerate(certifications):
                      st.markdown('<div class="roadmap-goal-item">', unsafe_allow_html=True)
                      title = cert.get('title','Certification')
                      desc = cert.get('description', 'N/A')
                      url = cert.get('url', '#')
                      st.markdown(f"**📜 {title}**")
                      st.markdown(f"<div class='roadmap-goal-description'>{desc}</div>", unsafe_allow_html=True)
                      if url and url != "#": st.markdown(f"**Learn More:** [{title} Link]({url})", unsafe_allow_html=True)
                      st.markdown('</div>', unsafe_allow_html=True)
                      if idx < cert_count - 1:
                          st.markdown('<hr class="roadmap-separator">', unsafe_allow_html=True)

        else:
             st.markdown('<p class="neutral-feedback" style="margin-top: 1rem;">No specific certifications recommended.</p>', unsafe_allow_html=True)


        # --- Projects ---
        if projects := result.get("projects"):
             with st.expander("Suggested Projects"):
                 project_count = len(projects)
                 for idx, project in enumerate(projects):
                      st.markdown('<div class="roadmap-goal-item">', unsafe_allow_html=True)
                      title = project.get('title','Project')
                      level = project.get('level', 'N/A')
                      desc = project.get('description','N/A')
                      tech = project.get("technologies", [])
                      url = project.get('url')

                      st.markdown(f"**💡 {title} ({level})**")
                      st.markdown(f"<div class='roadmap-goal-description'>{desc}</div>", unsafe_allow_html=True)
                      if tech: st.markdown(f"**Technologies:** `{', '.join(tech)}`")
                      if url: st.markdown(f"**Example/Info:** {url}") # Display URL plainly if present
                      st.markdown('</div>', unsafe_allow_html=True)
                      if idx < project_count - 1:
                           st.markdown('<hr class="roadmap-separator">', unsafe_allow_html=True)
        else:
            st.markdown('<p class="neutral-feedback" style="margin-top: 1rem;">No specific projects suggested.</p>', unsafe_allow_html=True)


        # --- Download Roadmap ---
        try:
            # Ensure rec_role is defined before using it in filename
            if 'rec_role' not in locals(): rec_role = result.get('recommended_role', 'recommendation')
            rec_role_filename = rec_role.replace(' ','_').replace('/','-')[:25]
            result_json = json.dumps(result, indent=2)
            st.download_button("⬇️ Download Recommendation (JSON)", result_json, f"job_recommendation_{rec_role_filename}.json", "application/json", key="download_job_rec_roadmap")
        except Exception as e: st.error(f"Could not prepare recommendation for download: {e}")

    except Exception as e:
        st.error(f"Error displaying job recommendation: {e}")
        st.exception(e)
        st.json(result if isinstance(result, dict) else {"error": "Data is not a dictionary"})


# --- display_career_roadmap ---
def display_career_roadmap(roadmap_data):
    """Displays the structured career roadmap JSON data in a user-friendly format."""
    if not roadmap_data or not isinstance(roadmap_data, dict):
        st.error("Invalid or missing roadmap data received.")
        if isinstance(roadmap_data, dict) and "error" in roadmap_data:
             st.code(roadmap_data.get("raw_text", "No raw text available from failed generation."))
        return

    try:
        st.markdown('<div class="ats-section-card"><h4><span style="font-size: 1.5em;">🗺️</span> Your Personalized Career Roadmap</h4></div>', unsafe_allow_html=True)

        rec_focus = roadmap_data.get('recommended_focus_area', 'N/A')
        justification = roadmap_data.get('justification', 'N/A')
        st.markdown("##### Recommended Focus & Justification")
        st.markdown(f"<div class='suggestion-card' style='margin-bottom: 1.5rem;'><b>Focus Area:</b> {rec_focus}<br><b>Justification:</b> {justification}</div>", unsafe_allow_html=True)

        roadmap = roadmap_data.get('roadmap', {})
        if roadmap:
            st.markdown("##### Roadmap Timeline")
            timeline_tabs = st.tabs(["➡️ Short Term (1-2 Yrs)", "⏳ Mid Term (3-5 Yrs)", "🚀 Long Term (5+ Yrs)"])
            timeframe_keys = ["short_term (1-2 Years)", "mid_term (3-5 Years)", "long_term (5+ Years)"]

            for i, key in enumerate(timeframe_keys):
                with timeline_tabs[i]:
                    goals = roadmap.get(key, [])
                    if goals:
                        goal_count = len(goals)
                        for idx, goal in enumerate(goals):
                            st.markdown('<div class="roadmap-goal-item">', unsafe_allow_html=True)
                            icon = goal.get('icon', '🎯'); title = goal.get('title', 'Goal')
                            desc = goal.get("description", "")
                            st.markdown(f'<div class="roadmap-goal-title"><span>{icon}</span> {title}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="roadmap-goal-description">{desc}</div>', unsafe_allow_html=True)

                            if resources := goal.get("resources"):
                                st.markdown('<div class="roadmap-goal-resources"><h6>Resources:</h6><ul>', unsafe_allow_html=True)
                                for res in resources:
                                    res_title = res.get('title', '[Resource]')
                                    if res_url := res.get('url'):
                                        if res_url != "#": st.markdown(f'<li><a href="{res_url}" target="_blank">{res_title}</a></li>', unsafe_allow_html=True)
                                        else: st.markdown(f'<li>{res_title}</li>', unsafe_allow_html=True)
                                    else: st.markdown(f'<li>{res_title}</li>', unsafe_allow_html=True)
                                st.markdown('</ul></div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True) # end goal-item
                            if idx < goal_count - 1:
                                st.markdown('<hr class="roadmap-separator">', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="neutral-feedback">No specific goals outlined for the {key.split("(")[0].strip()}.</p>', unsafe_allow_html=True)
        else:
            st.warning("Roadmap timeline details not found in the generated data.")

        if skills_dev := roadmap_data.get('key_skills_to_develop'):
            st.markdown('<h5 class="subsection-heading">Key Skills to Develop</h5>', unsafe_allow_html=True)
            num_cols = min(len(skills_dev), 2)
            cols = st.columns(num_cols) if num_cols > 0 else [st]
            for idx, category_data in enumerate(skills_dev):
                 with cols[idx % num_cols]:
                     category_title = category_data.get('category', 'Skills')
                     st.markdown(f"<div class='skills-category'><h6>{category_title}</h6>", unsafe_allow_html=True)
                     if skills := category_data.get('skills'):
                          st.markdown("<ul>" + "".join([f"<li>{skill}</li>" for skill in skills]) + "</ul>", unsafe_allow_html=True)
                     else: st.markdown("<ul><li>N/A</li></ul>", unsafe_allow_html=True)
                     st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Key skills to develop not specified.")

        try:
            focus_filename = rec_focus.replace(' ','_').replace('/','-')[:25]
            roadmap_json_str = json.dumps(roadmap_data, indent=2)
            st.download_button("⬇️ Download Roadmap Data (JSON)", roadmap_json_str, f"career_roadmap_{focus_filename}.json", "application/json", key="download_roadmap_json")
        except Exception as e: st.error(f"Could not prepare roadmap data for download: {e}")

    except Exception as e:
        st.error(f"Error displaying structured career roadmap: {str(e)}")
        st.exception(e)
        st.json(roadmap_data if isinstance(roadmap_data, dict) else {"error": "Data is not a dictionary"})


# --- display_ats_optimization_results ---
def display_ats_optimization_results(results):
    """Displays the comprehensive ATS optimization results using a tabbed interface."""
    if not results or not isinstance(results, dict):
        st.warning("No ATS optimization results available to display.")
        return

    try:
        st.markdown('<h3 class="section-heading">🎯 ATS Optimization Analysis</h3>', unsafe_allow_html=True)
        tab_content, tab_structure, tab_completeness, tab_enhance = st.tabs(["📄 Content Analysis", "🏗️ Structure & Formatting", "✅ Completeness", "✨ Enhancements"])

        ai_checks = results.get("ai_checks", {}); standard_checks = results.get("standard_checks", {})
        layout_data = results.get("layout_analysis", {}); enhancement_suggestions = results.get("enhancement_suggestions", {})

        with tab_content:
            st.markdown('<div class="ats-section-card" style="margin-bottom: 0.5rem;"><h4>Content & Language Review</h4></div>', unsafe_allow_html=True)
            with st.container(): # Spelling & Grammar
                st.markdown('<div class="ats-check-title">Spelling & Grammar</div>', unsafe_allow_html=True)
                grammar_data = ai_checks.get("spelling_grammar", {}); errors = grammar_data.get("errors", []); message = grammar_data.get("message", "")
                if errors:
                    st.markdown('<p class="negative-feedback">Potential errors found:</p>', unsafe_allow_html=True)
                    for error in errors:
                         original = error.get('original','N/A'); corrected = error.get('corrected','N/A'); explanation = error.get('explanation', 'N/A')
                         st.markdown(f"""<div class="correction-block"><span class="original">Original: {original}</span><span class="corrected">Corrected: {corrected}</span><span class="explanation">Explanation: {explanation}</span></div>""", unsafe_allow_html=True)
                elif message: st.markdown(f'<div class="suggestion-card-green">✅ {message}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="suggestion-card-green">✅ No significant errors found.</div>', unsafe_allow_html=True)
            with st.container(): # Word Repetition
                st.markdown('<div class="ats-check-title">Word Repetition</div>', unsafe_allow_html=True)
                repetition_data = ai_checks.get("repetition", {}); repeated = repetition_data.get("repeated_words", []); message = repetition_data.get("message", "")
                if repeated:
                    st.markdown('<p class="negative-feedback">Frequent word usage detected:</p>', unsafe_allow_html=True)
                    with st.expander("View Details", expanded=len(repeated) < 4):
                        for item in repeated:
                            word = item.get('word', 'N/A'); count = item.get('count', 0); suggestions = item.get('suggestions', []); suggestion_str = ', '.join(suggestions) if suggestions else 'N/A'
                            st.markdown(f"""<div class="repetition-item"><span class="word">"{word}"</span> ({count} times)<div class="suggestions">Suggestions: {suggestion_str}</div></div>""", unsafe_allow_html=True)
                elif message: st.markdown(f'<div class="suggestion-card-green">✅ {message}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="suggestion-card-green">✅ No significant repetition found.</div>', unsafe_allow_html=True)
            with st.container(): # Active Voice
                st.markdown('<div class="ats-check-title">Active vs. Passive Voice</div>', unsafe_allow_html=True)
                active_voice_data = ai_checks.get("active_voice", {}); passive = active_voice_data.get("passive_sentences", []); message = active_voice_data.get("message", "")
                if passive:
                    st.markdown('<p class="negative-feedback">Potential passive voice:</p>', unsafe_allow_html=True)
                    with st.expander("View Details", expanded=len(passive) < 4):
                        for item in passive:
                             original = item.get('original','N/A'); active_sug = item.get('active','N/A')
                             st.markdown(f"""<div class="correction-block"><span class="original">Passive: {original}</span><span class="corrected">Active Suggestion: {active_sug}</span></div>""", unsafe_allow_html=True)
                elif message: st.markdown(f'<div class="suggestion-card-green">✅ {message}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="suggestion-card-green">✅ Good use of active voice.</div>', unsafe_allow_html=True)
            with st.container(): # Buzzwords
                st.markdown('<div class="ats-check-title">Buzzwords & Clichés</div>', unsafe_allow_html=True)
                buzzwords_found = standard_checks.get("buzzwords", [])
                if buzzwords_found:
                    highlighted = ", ".join([f'<span class="highlight-buzzword">{word}</span>' for word in buzzwords_found])
                    st.markdown(f'<div class="suggestion-card-red">⚠️ Buzzwords/clichés found: {highlighted}. Replace with specifics.</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="suggestion-card-green">✅ No common buzzwords detected.</div>', unsafe_allow_html=True)
            with st.container(): # Quantifiable Impact
                st.markdown('<div class="ats-check-title">Quantifiable Impact</div>', unsafe_allow_html=True)
                quantify_data = ai_checks.get("quantify_impact", {}); lacking = quantify_data.get("lacking_quantification", []); message = quantify_data.get("message", "")
                if lacking:
                    st.markdown('<p class="negative-feedback">Bullets lacking quantifiable results:</p>', unsafe_allow_html=True)
                    with st.expander("View Details", expanded=len(lacking) < 5):
                        for item in lacking:
                             bullet = item.get('bullet', 'N/A'); suggestion = item.get('suggestion', 'Add metrics.')
                             st.markdown(f"""<div class="suggestion-card"><p><strong>Bullet:</strong> {bullet}</p><p><strong>Suggestion:</strong> {suggestion}</p></div>""", unsafe_allow_html=True)
                elif message: st.markdown(f'<div class="suggestion-card-green">✅ {message}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="suggestion-card-green">✅ Good job quantifying impact.</div>', unsafe_allow_html=True)

        with tab_structure:
             st.markdown('<div class="ats-section-card" style="margin-bottom: 0.5rem;"><h4>Structure, Formatting & Brevity</h4></div>', unsafe_allow_html=True)
             st.markdown('<div class="ats-metric-row">', unsafe_allow_html=True)
             parse_rate = standard_checks.get('parse_rate', 'N/A'); pr_d = f"{parse_rate}%" if isinstance(parse_rate, int) else "N/A"; pr_help = "Est. ATS readability."
             st.markdown(f'<div class="ats-metric-item"><h5>ATS Parse Rate (Est.)</h5><p>{pr_d}</p><small>{pr_help}</small></div>', unsafe_allow_html=True)
             wc = standard_checks.get('resume_word_count', 'N/A'); np = layout_data.get('num_pages', 'N/A'); len_d = f"{wc} words" if isinstance(wc, int) else "N/A"; pg_d = f"{np} page(s)" if isinstance(np, (int, float)) and np > 0 else "N/A"; len_help = standard_checks.get("resume_length_feedback", "Aim 1-2 pages.")
             st.markdown(f'<div class="ats-metric-item"><h5>Length</h5><p>{len_d} / {pg_d}</p><small>{len_help}</small></div>', unsafe_allow_html=True)
             fs = layout_data.get('formatting_score', 'N/A'); fs_d = f"{fs}%" if isinstance(fs, int) else "N/A"; fs_help = "Est. ATS-friendly formatting."
             st.markdown(f'<div class="ats-metric-item"><h5>Formatting Score (Est.)</h5><p>{fs_d}</p><small>{fs_help}</small></div>', unsafe_allow_html=True)
             st.markdown('</div>', unsafe_allow_html=True)
             with st.container(): # Bullet Point Length
                st.markdown('<div class="ats-check-title">Bullet Point Length</div>', unsafe_allow_html=True)
                long_bullet_data = ai_checks.get("long_bullets", {}); long_bullets_found = long_bullet_data.get("long_bullets", []); message = long_bullet_data.get("message", "")
                if long_bullets_found:
                    st.markdown('<p class="negative-feedback">Overly long bullet points found:</p>', unsafe_allow_html=True)
                    with st.expander("View Details", expanded=len(long_bullets_found) < 4):
                        for item in long_bullets_found:
                             bullet = item.get('bullet', 'N/A'); suggestion = item.get('suggestion', 'Shorten/split.')
                             st.markdown(f"""<div class="suggestion-card"><p><strong>Bullet:</strong> {bullet}</p><p><strong>Suggestion:</strong> {suggestion}</p></div>""", unsafe_allow_html=True)
                elif message: st.markdown(f'<div class="suggestion-card-green">✅ {message}</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="suggestion-card-green">✅ Bullets appear concise.</div>', unsafe_allow_html=True)
             with st.container(): # Layout Issues
                st.markdown('<div class="ats-check-title">Layout & Formatting Issues</div>', unsafe_allow_html=True)
                layout_issues = layout_data.get("layout_issues", [])
                if layout_issues:
                    st.markdown('<p class="neutral-feedback">Potential layout issues/considerations:</p>', unsafe_allow_html=True)
                    with st.expander("View Details", expanded=True):
                        for issue in layout_issues: st.markdown(f'<div class="suggestion-card">⚠️ {issue}</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="suggestion-card-green">✅ No major layout issues detected.</div>', unsafe_allow_html=True)

        with tab_completeness:
             st.markdown('<div class="ats-section-card" style="margin-bottom: 0.5rem;"><h4>Resume Section Completeness</h4></div>', unsafe_allow_html=True)
             with st.container(): # Contact Information
                st.markdown('<div class="ats-check-title">Contact Information</div>', unsafe_allow_html=True)
                contact_info = standard_checks.get("contact_information", {})
                has_email = 'email_address' in contact_info and contact_info['email_address']
                has_phone = 'phone_number' in contact_info and contact_info['phone_number']
                if has_email and has_phone: st.markdown('<div class="suggestion-card-green">✅ Essential contact info (Email & Phone) found.</div>', unsafe_allow_html=True)
                elif has_email or has_phone: missing = "Phone" if not has_phone else "Email"; st.markdown(f'<div class="suggestion-card-red">⚠️ Missing essential contact info ({missing}).</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="suggestion-card-red">❌ Crucial contact info (Email & Phone) missing.</div>', unsafe_allow_html=True)

                details_html = "<h6>Detected Information:</h6><ul>"
                if contact_info.get('email_address'):
                    email_text = f"<li>**Email:** {contact_info['email_address']}"
                    if 'email_warning' in contact_info: email_text += f" <span style='color:orange;font-size:0.9em;'><i>({contact_info['email_warning']})</i></span>"
                    details_html += email_text + "</li>"
                else: details_html += "<li><span class='negative-feedback'>**Email:** Missing/Not Found</span></li>"
                if contact_info.get('phone_number'): details_html += f"<li>**Phone:** {contact_info['phone_number']}</li>"
                else: details_html += "<li><span class='negative-feedback'>**Phone:** Missing/Not Found</span></li>"
                if contact_info.get('location'): details_html += f"<li>**Location:** {contact_info['location']}</li>"
                if contact_info.get('linkedin_url'): details_html += f"<li>**LinkedIn:** {contact_info['linkedin_url']}</li>"
                if contact_info.get('github_url'): details_html += f"<li>**GitHub:** {contact_info['github_url']}</li>"
                if contact_info.get('portfolio_url'): details_html += f"<li>**Portfolio/Website:** {contact_info['portfolio_url']}</li>"
                details_html += "</ul>"
                st.markdown(details_html, unsafe_allow_html=True)
             with st.container(): # Essential Sections
                st.markdown('<div class="ats-check-title">Essential Sections</div>', unsafe_allow_html=True)
                sections_found = standard_checks.get("essential_sections_found", []); sections_missing = standard_checks.get("essential_sections_missing", [])
                if not sections_missing:
                    st.markdown('<div class="suggestion-card-green">✅ All essential sections seem present.</div>', unsafe_allow_html=True)
                    if sections_found: st.markdown(f'<p class="neutral-feedback" style="font-size:0.9em;"><i>Detected: {", ".join(sections_found)}.</i></p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="suggestion-card-red">⚠️ Potentially Missing Sections: <strong>{", ".join(sections_missing)}</strong>. Use clear titles.</div>', unsafe_allow_html=True)
                    if sections_found: st.markdown(f'<p class="neutral-feedback" style="font-size:0.9em;"><i>Detected: {", ".join(sections_found)}.</i></p>', unsafe_allow_html=True)
             with st.container(): # Hobbies/Interests
                st.markdown('<div class="ats-check-title">Hobbies / Interests / Personal</div>', unsafe_allow_html=True)
                hobbies_data = ai_checks.get("hobbies", {}); found = hobbies_data.get("found", False); analysis = hobbies_data.get("analysis", ""); suggestions = hobbies_data.get("suggestions", [])
                if found:
                    st.markdown(f'<div class="suggestion-card-green">✅ Hobbies/Interests section detected.</div>', unsafe_allow_html=True)
                    if analysis: st.markdown(f"<p class='neutral-feedback' style='font-size:0.95em;'><i>AI Analysis: {analysis}</i></p>", unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="suggestion-card">💡 Hobbies section not detected. Optional, consider if relevant. {analysis or ""}</div>', unsafe_allow_html=True)
                    if suggestions:
                        with st.expander("View Hobby/Interest Suggestions"):
                             for s in suggestions: st.markdown(f"- {s}")

        with tab_enhance:
             st.markdown('<div class="ats-section-card" style="margin-bottom: 0.5rem;"><h4>✨ AI-Powered Enhancement Suggestions</h4></div>', unsafe_allow_html=True)
             st.markdown("<p class='neutral-feedback' style='font-size:0.95em; margin-bottom: 1rem;'><i>Detailed suggestions to improve resume content, structure, and impact.</i></p>", unsafe_allow_html=True)
             if enhancement_suggestions and isinstance(enhancement_suggestions, dict) and enhancement_suggestions.get('summary_section'):
                 with st.container(): display_enhancement_suggestions(enhancement_suggestions)
             else: st.warning("No specific AI enhancement suggestions were generated or data is invalid.")

        st.markdown("---")

    except Exception as e:
        st.error(f"Error displaying ATS optimization results: {str(e)}")
        st.exception(e)
        st.json(results)

# --- End of display.py ---