# dashboard.py (COMPLETE - Updates in fetch_job_data_and_options AND show_dashboard)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from supabase import create_client, Client
from datetime import datetime, timedelta
import matplotlib.colors as mcolors
import numpy as np
import re
import logging # Import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- List of Indian States (for filtering during city extraction) ---
INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "andaman and nicobar islands", "chandigarh",
    "dadra and nagar haveli and daman and diu", "delhi",
    "jammu and kashmir", "ladakh", "lakshadweep", "puducherry"
]


# --- Function to fetch data and options ---
@st.cache_data(ttl=3600)
def fetch_job_data_and_options():
    logging.info("Attempting to fetch job data and options from Supabase.")
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        response = supabase.table('jobs').select(
            'job_id, position, company, location, rating, reviews_count, salary, job_url, company_url, posting_date, scraped_at, is_expired'
        ).execute()
        logging.info(f"Supabase query executed. Response received: {'Data received' if response.data else 'No data'}")

        if not response.data:
            # ... (keep existing no-data handling logic) ...
            count_response = supabase.table('jobs').select('job_id', count='exact').limit(0).execute() # Efficient count
            logging.info(f"Attempting count query. Count: {count_response.count}")
            if count_response.count == 0:
                logging.warning("The 'jobs' table exists but contains no data.")
                # Return empty DataFrame and default options
                default_options = {
                    'companies': ['All'], 'positions': ['All'], 'cities': ['All'],
                    'min_date': datetime.now().date() - timedelta(days=30),
                    'max_date': datetime.now().date()
                }
                return pd.DataFrame(), default_options
            else:
                 logging.error("Supabase returned no data, but table is not empty. Check permissions or query.")
                 raise Exception("Supabase returned no data, but table is not empty. Check permissions or query.")


        jobs_df = pd.DataFrame(response.data)
        logging.info(f"Successfully loaded {len(jobs_df)} rows into DataFrame.")

        # --- Data Cleaning and Transformation ---
        initial_rows = len(jobs_df)

        # Date Columns... (keep as is)
        for date_col in ['posting_date', 'scraped_at']:
            if date_col in jobs_df.columns:
                original_type = jobs_df[date_col].dtype
                jobs_df[date_col] = pd.to_datetime(jobs_df[date_col], errors='coerce')
                rows_dropped = initial_rows - len(jobs_df.dropna(subset=[date_col]))
                if rows_dropped > 0:
                    logging.warning(f"Dropped {rows_dropped} rows due to invalid dates in '{date_col}'. Original type: {original_type}")
                jobs_df.dropna(subset=[date_col], inplace=True)
            else:
                logging.warning(f"Expected date column '{date_col}' not found.")


        # Numeric Columns... (keep as is)
        for num_col in ['rating', 'reviews_count']:
             if num_col in jobs_df.columns:
                 jobs_df[num_col] = pd.to_numeric(jobs_df[num_col], errors='coerce').fillna(0)
             else:
                 logging.warning(f"Expected numeric column '{num_col}' not found.")


        # --- Location (City Extraction - ***REFINED***) ---
        if 'location' in jobs_df.columns:
            def extract_city(location_str):
                if pd.isna(location_str):
                    return 'Unknown'
                location_str = str(location_str).strip()
                parts = [p.strip() for p in location_str.split(',')]
                if not parts:
                    return 'Unknown'

                # Attempt 1: Take the first part if it's not a known state name (case-insensitive)
                first_part_lower = parts[0].lower()
                if first_part_lower and first_part_lower not in INDIAN_STATES:
                    # Basic check for overly specific sub-locations (can be expanded)
                    if 'sector' not in first_part_lower and 'nagar' not in first_part_lower:
                         return parts[0] # Return original case

                # Attempt 2: If first part was a state, try the second part
                if len(parts) > 1:
                    second_part_lower = parts[1].lower()
                    if second_part_lower and second_part_lower not in INDIAN_STATES:
                       if 'sector' not in second_part_lower and 'nagar' not in second_part_lower:
                            return parts[1] # Return original case

                # Fallback: Return the original first part if attempts failed or only one part existed
                return parts[0] if parts[0] else 'Unknown'

            jobs_df['city'] = jobs_df['location'].apply(extract_city)
            # Log a sample of extracted cities
            logging.info(f"Sample extracted cities: {jobs_df['city'].unique()[:20]}")
        else:
            logging.warning("Expected 'location' column for city extraction not found.")
            jobs_df['city'] = 'Unknown'

        # Job Title (Base Position)... (keep as is)
        if 'position' in jobs_df.columns:
             jobs_df['base_position'] = jobs_df['position'].astype(str).apply( # Convert to string first
                lambda x: re.sub(r'\b(Senior|Sr\.|Junior|Jr\.|Lead|Principal|Staff|Manager|Director|VP|Head of)\b|\s*\(.*?\)|[^a-zA-Z\s\d]', '', x, flags=re.IGNORECASE).strip()
                if pd.notna(x) else 'Unknown'
            ).str.title()
             jobs_df['base_position'] = jobs_df['base_position'].replace('', 'Unknown') # Replace empty strings after regex
        else:
            logging.warning("Expected 'position' column for base position extraction not found.")
            jobs_df['base_position'] = 'Unknown'


        # Job Expiration... (keep as is)
        if 'is_expired' in jobs_df.columns:
             if jobs_df['is_expired'].dtype == 'object':
                 jobs_df['is_expired'] = jobs_df['is_expired'].str.lower().map({'true': True, 'false': False}).fillna(False).astype(bool)
             else:
                 jobs_df['is_expired'] = pd.to_numeric(jobs_df['is_expired'], errors='coerce').fillna(0).astype(bool)
        else:
             logging.warning("Expected 'is_expired' column not found.")
             jobs_df['is_expired'] = False


        # Job Freshness... (keep as is)
        if 'posting_date' in jobs_df.columns and 'scraped_at' in jobs_df.columns:
             if pd.api.types.is_datetime64_any_dtype(jobs_df['posting_date']) and pd.api.types.is_datetime64_any_dtype(jobs_df['scraped_at']):
                 jobs_df['job_freshness_days'] = (jobs_df['scraped_at'] - jobs_df['posting_date']).dt.days
                 jobs_df['job_freshness_days'] = jobs_df['job_freshness_days'].clip(lower=0).fillna(0).astype(int)
             else:
                  logging.warning("Could not calculate job freshness due to incorrect date types.")
                  jobs_df['job_freshness_days'] = 0
        else:
             logging.warning("Expected 'posting_date' and 'scraped_at' for job freshness calculation.")
             jobs_df['job_freshness_days'] = 0


        logging.info(f"Data cleaning finished. Remaining rows: {len(jobs_df)}")

        # --- Calculate filter options --- (keep as is)
        min_date = jobs_df['posting_date'].min().date() if 'posting_date' in jobs_df.columns and not jobs_df.empty else datetime.now().date() - timedelta(days=90)
        max_date = jobs_df['posting_date'].max().date() if 'posting_date' in jobs_df.columns and not jobs_df.empty else datetime.now().date()

        filter_options = {
            'companies': ['All'] + sorted(jobs_df['company'].dropna().unique().tolist()) if 'company' in jobs_df.columns else ['All'],
            'positions': ['All'] + sorted(jobs_df['base_position'].dropna().unique().tolist()) if 'base_position' in jobs_df.columns else ['All'],
            'cities': ['All'] + sorted(jobs_df['city'].dropna().unique().tolist()) if 'city' in jobs_df.columns else ['All'], # Uses the refined 'city'
            'min_date': min_date,
            'max_date': max_date
        }
        logging.info("Filter options generated.")

        return jobs_df, filter_options # Return both df and options

    except Exception as e:
        logging.error(f"Error in fetch_job_data_and_options: {e}", exc_info=True)
        st.error(f"Error fetching or processing data from Supabase: {e}")
        # Return empty df and default options on failure
        default_options = {
            'companies': ['All'], 'positions': ['All'], 'cities': ['All'],
            'min_date': datetime.now().date() - timedelta(days=30),
            'max_date': datetime.now().date()
        }
        return pd.DataFrame(), default_options


# --- Main Dashboard Function ---
def show_dashboard():
    # ... (Keep existing code retrieving jobs_df from session state or fetching) ...
    if 'jobs_df' in st.session_state:
        jobs_df = st.session_state['jobs_df']
    else:
         logging.warning("jobs_df not found in session state, fetching again within show_dashboard.")
         jobs_df, _ = fetch_job_data_and_options()
         if jobs_df.empty:
             st.error("No job data available to display.")
             st.stop()
    if jobs_df.empty:
        st.error("No job data available to display.")
        st.stop()

    # ... (Keep ALL filtering logic based on session_state AS IS) ...
    logging.info(f"Starting dashboard filtering. Initial rows: {len(jobs_df)}")
    jobs_df_filtered = jobs_df.copy()
    # --- Date Range Filter ---
    date_range = st.session_state.get('dash_date', None)
    if 'posting_date' in jobs_df_filtered.columns and date_range and len(date_range) == 2:
        # ... (date filter code) ...
        try:
            start_date, end_date = date_range
            if start_date and end_date: # Ensure both dates are selected
                jobs_df_filtered = jobs_df_filtered[
                    (jobs_df_filtered['posting_date'].dt.date >= start_date) &
                    (jobs_df_filtered['posting_date'].dt.date <= end_date)
                ]
                logging.info(f"Applied date filter: {start_date} to {end_date}. Rows remaining: {len(jobs_df_filtered)}")
            else:
                 logging.info("Date range not fully selected, skipping date filter.")
        except Exception as e:
             logging.error(f"Error during date filtering: {e}")
             st.error(f"An unexpected error occurred during date filtering: {e}")
    elif 'posting_date' not in jobs_df_filtered.columns:
         logging.warning("Date filter skipped: 'posting_date' column missing.")

    # --- Company Filter ---
    selected_companies = st.session_state.get('dash_company', [])
    if 'company' in jobs_df_filtered.columns and selected_companies:
         # ... (company filter code) ...
        valid_companies = [c for c in selected_companies if c != 'All']
        if valid_companies:
            jobs_df_filtered = jobs_df_filtered[jobs_df_filtered['company'].isin(valid_companies)]
            logging.info(f"Applied company filter: {valid_companies}. Rows remaining: {len(jobs_df_filtered)}")
        else:
            logging.info("No specific companies selected, skipping company filter.")
    elif 'company' not in jobs_df_filtered.columns:
         logging.warning("Company filter skipped: 'company' column missing.")


    # --- Position Filter ---
    selected_positions = st.session_state.get('dash_title', [])
    if 'base_position' in jobs_df_filtered.columns and selected_positions:
        # ... (position filter code) ...
        valid_positions = [p for p in selected_positions if p != 'All']
        if valid_positions:
             jobs_df_filtered = jobs_df_filtered[jobs_df_filtered['base_position'].isin(valid_positions)]
             logging.info(f"Applied position filter: {valid_positions}. Rows remaining: {len(jobs_df_filtered)}")
        else:
             logging.info("No specific positions selected, skipping position filter.")
    elif 'base_position' not in jobs_df_filtered.columns:
        logging.warning("Job title filter skipped: 'base_position' column missing.")


    # --- Location Filter ---
    selected_cities = st.session_state.get('dash_location', [])
    if 'city' in jobs_df_filtered.columns and selected_cities:
        # ... (location filter code) ...
        valid_cities = [city for city in selected_cities if city != 'All']
        if valid_cities:
            jobs_df_filtered = jobs_df_filtered[jobs_df_filtered['city'].isin(valid_cities)]
            logging.info(f"Applied city filter: {valid_cities}. Rows remaining: {len(jobs_df_filtered)}")
        else:
            logging.info("No specific cities selected, skipping city filter.")
    elif 'city' not in jobs_df_filtered.columns:
        logging.warning("Location filter skipped: 'city' column missing.")


    # --- Job Status Filter ---
    job_status = st.session_state.get('dash_status', "All")
    if 'is_expired' in jobs_df_filtered.columns:
        # ... (status filter code) ...
        if job_status == "Active":
            jobs_df_filtered = jobs_df_filtered[~jobs_df_filtered['is_expired']]
            logging.info(f"Applied status filter: Active. Rows remaining: {len(jobs_df_filtered)}")
        elif job_status == "Expired":
            jobs_df_filtered = jobs_df_filtered[jobs_df_filtered['is_expired']]
            logging.info(f"Applied status filter: Expired. Rows remaining: {len(jobs_df_filtered)}")
        else:
            logging.info("Status filter: All.")
    elif 'is_expired' not in jobs_df_filtered.columns:
        logging.warning("Job status filter skipped: 'is_expired' column missing.")

    # ------------------------------------------
    # MAIN DASHBOARD AREA - Visualizations start
    # ------------------------------------------
    st.title("📊 Job Market Insights Dashboard")
    # ... (Keep Key Metrics, Job Posting Trends, Top Hiring Companies, Most Popular Roles AS IS) ...
    st.markdown(f"""
    Displaying insights for **{len(jobs_df_filtered)}** job postings based on the selected filters.
    Use the filters on the sidebar to refine your analysis.
    """)
    # ... KEY METRICS ...
    st.markdown("## 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    # ... (metrics code) ...
    with col1: st.metric("Filtered Jobs", len(jobs_df_filtered))
    with col2:
        if 'is_expired' in jobs_df_filtered.columns:
            active_jobs_count = len(jobs_df_filtered[~jobs_df_filtered['is_expired']])
            st.metric("Active Jobs", active_jobs_count)
        else: st.metric("Active Jobs", "N/A", help="'is_expired' column missing")
    with col3:
        if 'company' in jobs_df_filtered.columns:
            unique_companies_count = jobs_df_filtered['company'].nunique()
            st.metric("Companies Hiring", unique_companies_count)
        else: st.metric("Companies Hiring", "N/A", help="'company' column missing")
    with col4:
        if 'rating' in jobs_df_filtered.columns and not jobs_df_filtered.empty:
             valid_ratings = jobs_df_filtered[jobs_df_filtered['rating'] > 0]['rating']
             avg_rating = round(valid_ratings.mean(), 2) if not valid_ratings.empty else 0
             st.metric("Avg. Rating", avg_rating if avg_rating > 0 else "N/A", help="Average rating for companies with ratings > 0 in filtered results.")
        elif 'rating' not in jobs_df_filtered.columns: st.metric("Avg. Rating", "N/A", help="'rating' column missing")
        else: st.metric("Avg. Rating", "N/A", help="No jobs match filters")

    # ... JOB POSTING TRENDS ...
    st.markdown("## 📅 Job Posting Trends")
    # ... (trends code) ...
    if not jobs_df_filtered.empty:
        col1_trends, col2_trends = st.columns(2) # Use different names to avoid conflict
        with col1_trends:
            # (Plotting code for posting_trends - Keep as is, operates on jobs_df_filtered)
            if 'posting_date' in jobs_df_filtered.columns and pd.api.types.is_datetime64_any_dtype(jobs_df_filtered['posting_date']):
                posting_trends = jobs_df_filtered.resample('D', on='posting_date').size().reset_index(name='count') # Resample for continuous timeline
                posting_trends.columns = ['date', 'count']

                fig_trend = px.line(
                    posting_trends, x='date', y='count',
                    title='Job Postings Over Time (Filtered)',
                    labels={'date': 'Posting Date', 'count': 'Number of Jobs'}, markers=True
                )
                fig_trend.update_layout(height=400)
                st.plotly_chart(fig_trend, use_container_width=True)
            else: st.write("Job posting trends not available (missing/invalid 'posting_date').")

        with col2_trends:
            # (Plotting code for job_freshness - Keep as is, operates on jobs_df_filtered)
            if 'job_freshness_days' in jobs_df_filtered.columns:
                fig_freshness = px.histogram(
                    jobs_df_filtered, x='job_freshness_days',
                    title='Job Freshness (Days Since Posting - Filtered)',
                    labels={'job_freshness_days': 'Days Since Posting', 'count': 'Number of Jobs'},
                    nbins=20, color_discrete_sequence=['#3366CC']
                )
                fig_freshness.update_layout(height=400)
                st.plotly_chart(fig_freshness, use_container_width=True)
            else: st.write("Job freshness info not available (missing 'job_freshness_days').")
    else:
         st.markdown("<p class='neutral-feedback'>No job posting trend data available for the selected filters.</p>", unsafe_allow_html=True)


    # ... TOP HIRING COMPANIES ...
    st.markdown("## 🏢 Top Hiring Companies")
    # ... (companies code) ...
    if not jobs_df_filtered.empty and 'company' in jobs_df_filtered.columns:
        col1_comp, col2_comp = st.columns(2)
        # ... (bar chart) ...
        with col1_comp:
            # Get top companies by job count from the *filtered* DataFrame
            top_companies = jobs_df_filtered['company'].value_counts().reset_index()
            top_companies.columns = ['company', 'count']
            top_companies = top_companies.sort_values('count', ascending=False).head(10)

            if not top_companies.empty:
                fig_companies = px.bar(
                    top_companies, x='count', y='company',
                    title='Top 10 Hiring Companies (Filtered)',
                    labels={'count': 'Number of Jobs', 'company': 'Company'},
                    orientation='h', color='count', color_continuous_scale='Blues'
                )
                fig_companies.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_companies, use_container_width=True)
            else:
                st.write("No company data to display.")
        # ... (pie chart) ...
        with col2_comp:
            # Prepare data for pie chart from the *filtered* DataFrame
            company_distribution = jobs_df_filtered['company'].value_counts().reset_index()
            company_distribution.columns = ['company', 'count']

            # Group smaller companies as "Others" if needed
            if len(company_distribution) > 8:
                threshold = company_distribution['count'].sum() * 0.02
                other_companies = company_distribution[company_distribution['count'] < threshold]
                if not other_companies.empty:
                    company_distribution = company_distribution[company_distribution['count'] >= threshold]
                    company_distribution = pd.concat([
                        company_distribution,
                        pd.DataFrame([{'company': 'Others', 'count': other_companies['count'].sum()}])
                    ], ignore_index=True)

            if not company_distribution.empty:
                fig_company_pie = px.pie(
                    company_distribution, values='count', names='company',
                    title='Job Postings by Company (Filtered)', hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig_company_pie.update_layout(height=400)
                fig_company_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                st.plotly_chart(fig_company_pie, use_container_width=True)
            else:
                 st.write("No company data for pie chart.")
    elif 'company' not in jobs_df_filtered.columns:
        st.markdown("<p class='neutral-feedback'>Top hiring companies information not available (missing 'company' column).</p>", unsafe_allow_html=True)
    else: # If jobs_df_filtered is empty
        st.markdown("<p class='neutral-feedback'>No company data available for the selected filters.</p>", unsafe_allow_html=True)

    # ... MOST POPULAR JOB ROLES ...
    st.markdown("## 👨‍💻 Most Popular Job Roles")
    # ... (roles code) ...
    if not jobs_df_filtered.empty:
        col1_roles, col2_roles = st.columns(2)
        with col1_roles:
            if 'base_position' in jobs_df_filtered.columns:
                top_positions = jobs_df_filtered['base_position'].value_counts().reset_index()
                top_positions.columns = ['position', 'count']
                top_positions = top_positions.sort_values('count', ascending=False).head(10)

                if not top_positions.empty:
                    fig_positions = px.bar(
                        top_positions, x='count', y='position',
                        title='Top 10 Job Titles (Filtered)',
                        labels={'count': 'Number of Jobs', 'position': 'Job Title'},
                        orientation='h', color='count', color_continuous_scale='Greens'
                    )
                    fig_positions.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_positions, use_container_width=True)
                else:
                    st.write("No job title data to display.")
            else: st.write("Job title distribution not available (missing 'base_position').")

        with col2_roles:
            if 'position' in jobs_df_filtered.columns:
                st.subheader("Job Titles Word Cloud (Filtered)")
                position_text = ' '.join(jobs_df_filtered['position'].dropna().astype(str)) # Ensure string conversion

                if position_text.strip():
                    try:
                        wordcloud = WordCloud(
                            width=800, height=380, background_color='white',
                            colormap='viridis', max_words=100, collocations=False
                        ).generate(position_text)
                        fig_wordcloud, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig_wordcloud)
                    except Exception as wc_error: st.error(f"Could not generate word cloud: {wc_error}")
                else: st.write("Not enough text data for word cloud in filtered results.")
            else: st.write("Word cloud not available (missing 'position').")
    else:
         st.markdown("<p class='neutral-feedback'>No job role data available for the selected filters.</p>", unsafe_allow_html=True)

    # --------------------------
    # LOCATION INSIGHTS (***UPDATED Dictionary Here***)
    # --------------------------
    st.markdown("## 📍 Location Insights")

    if not jobs_df_filtered.empty and 'city' in jobs_df_filtered.columns:
        col1_loc, col2_loc, col3_loc = st.columns(3)

        # --- Bar and Pie Charts (No changes needed here) ---
        # ... (keep existing bar chart code for col1_loc) ...
        with col1_loc:
            top_locations = jobs_df_filtered['city'].value_counts().reset_index()
            top_locations.columns = ['city', 'count']
            top_locations = top_locations.sort_values('count', ascending=False).head(10)
            if not top_locations.empty:
                fig_locations = px.bar(
                    top_locations, x='count', y='city', title='Top 10 Cities (Filtered)',
                    labels={'count': 'Number of Jobs', 'city': 'City'}, orientation='h',
                    color='count', color_continuous_scale='Reds'
                )
                fig_locations.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_locations, use_container_width=True)
            else: st.write("No location data for bar chart.")

        # ... (keep existing pie chart code for col2_loc) ...
        with col2_loc:
            location_distribution = jobs_df_filtered['city'].value_counts().reset_index()
            location_distribution.columns = ['city', 'count']
            if len(location_distribution) > 8:
                threshold = location_distribution['count'].sum() * 0.02
                other_locations = location_distribution[location_distribution['count'] < threshold]
                if not other_locations.empty:
                    location_distribution = location_distribution[location_distribution['count'] >= threshold]
                    location_distribution = pd.concat([
                        location_distribution,
                        pd.DataFrame([{'city': 'Others', 'count': other_locations['count'].sum()}])
                    ], ignore_index=True)
            if not location_distribution.empty:
                fig_location_pie = px.pie(
                    location_distribution, values='count', names='city',
                    title='Postings by Location (Filtered)', hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Reds_r
                )
                fig_location_pie.update_layout(height=400)
                fig_location_pie.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                st.plotly_chart(fig_location_pie, use_container_width=True)
            else: st.write("No location data for pie chart.")

        # --- Map Visualization (Expanded Dictionary) ---
        with col3_loc:
            location_counts = jobs_df_filtered['city'].value_counts().reset_index()
            location_counts.columns = ['city', 'count']
            logging.info(f"Top 10 location counts before mapping:\n{location_counts.head(10)}")

            # --- *** FURTHER EXPANDED city_to_lat_lon Dictionary *** ---
            city_to_lat_lon = {
                # Major Metros & Variations
                'Bangalore': (12.9716, 77.5946), 'Bengaluru': (12.9716, 77.5946),
                'Hyderabad': (17.3850, 78.4867), 'Secunderabad': (17.4399, 78.4983),
                'Mumbai': (19.0760, 72.8777), 'Navi Mumbai': (19.0330, 73.0297), 'Thane': (19.2183, 72.9781),
                'Delhi': (28.7041, 77.1025), 'New Delhi': (28.6139, 77.2090),
                'Noida': (28.5355, 77.3910), 'Greater Noida': (28.4744, 77.5040), # Added
                'Gurugram': (28.4595, 77.0266), 'Gurgaon': (28.4595, 77.0266),
                'Chennai': (13.0827, 80.2707),
                'Pune': (18.5204, 73.8567), 'Chakan': (18.7550, 73.8235), # Near Pune, Added
                'Hinjawadi': (18.5913, 73.7389), # Pune IT Park, Added (Approx) - Alias for Pune?
                'Hinjewadi': (18.5913, 73.7389), # Pune IT Park, Added (Approx) - Alias for Pune?
                'Kolkata': (22.5726, 88.3639),
                'Ahmedabad': (23.0225, 72.5714), 'Gandhinagar': (23.2156, 72.6369),

                # Other Significant Cities (From logs + previous)
                'Jaipur': (26.9124, 75.7873),
                'Lucknow': (26.8467, 80.9462),
                'Chandigarh': (30.7333, 76.7794), 'Mohali': (30.7046, 76.7179), 'Panchkula': (30.6917, 76.8483), # Added
                'Visakhapatnam': (17.6868, 83.2185), 'Vijayawada': (16.5062, 80.6480),
                'Tirupati': (13.6288, 79.4192), # Added
                'Coimbatore': (11.0168, 76.9558), 'Madurai': (9.9252, 78.1198),
                'Tiruchchirappalli': (10.7905, 78.7047), # Added
                'Vellore': (12.9165, 79.1325), # Added
                'Indore': (22.7196, 75.8577), 'Bhopal': (23.2599, 77.4126),
                'Bhubaneswar': (20.2961, 85.8245), 'Cuttack': (20.4625, 85.8830),
                'Guwahati': (26.1445, 91.7362),
                'Shiliguri':(26.7271,88.3953), #Added
                'Patna': (25.5941, 85.1376), 'Ranchi': (23.3441, 85.3096),
                'Kochi': (9.9312, 76.2673), 'Cochin': (9.9312, 76.2673),
                'Kakkanad': (10.0269, 76.3079), # Near Kochi, Added (Approx) - Alias for Kochi?
                'Infopark-Kochi': (10.0098, 76.3512), # Specific area in Kochi, map to Kochi? (Using Kochi coords)
                'Thiruvananthapuram': (8.5241, 76.9366), 'Trivandrum': (8.5241, 76.9366),
                'Calicut': (11.2588, 75.7804), 'Kozhikode': (11.2588, 75.7804),
                'Thrissur': (10.5276, 76.2144), # Added
                'Mannarakkat': (10.9938, 76.4605), # Kerala, Added (Palakkad district)
                'Mysore': (12.2958, 76.6394), 'Mangalore': (12.9141, 74.8560),
                'Kolar': (13.1342, 78.1319),
                'Nagpur': (21.1458, 79.0882), 'Nashik': (19.9975, 73.7898), # Added
                'Vadodara': (22.3072, 73.1812), 'Surat': (21.1702, 72.8311),
                'Vapi': (20.3783, 72.9081), 'Navsari': (20.9519, 72.9323), # Added
                'Goa': (15.2993, 74.1240), 'Panaji': (15.4909, 73.8278), 'Mormugao': (15.4059, 73.8033),
                'Verna': (15.3613, 73.9307), # Goa, Added
                'Dehradun': (30.3165, 78.0322), # Added

                # Generic / Non-mappable
                'Remote': (None, None),
                'India': (None, None), # Often used generically
                'Multiple Locations': (None, None),
                'Unknown': (None, None),

                # Areas to potentially map to parent city or ignore (Assigning parent coords for now)
                'Gachibowli': (17.4401, 78.3489), # Hyderabad Area
                'Andheri': (19.1197, 72.8464), # Mumbai Area
                'Goregaon': (19.1649, 72.8485), # Mumbai Area
                'Vesu': (21.1333, 72.7797), # Surat Area
                'Kalyani Nagar': (18.5428, 73.9010), # Pune Area
                'Chikhli':(20.7742, 73.0445), # Navsari/Gujarat Area (Check context if possible)
                'Maduravoyal': (13.0658, 80.1682), # Chennai Area
                'Uttarahalli': (12.9097, 77.5497), # Bengaluru Area
                'Singanayakanahalli': (13.1353, 77.5859), # Bengaluru Area
                'Gautam Budh Nagar': (28.5355, 77.3910), # District - Map to Noida?
                'Noida Sector 62': (28.6180, 77.3678), # Noida Area
                'Ayodhya Nagar': (23.2213, 77.4700), # Bhopal Area? (Check context)
                'Purasawalkam': (13.0864, 80.2513), # Chennai Area

                # Explicitly ignore states by mapping to None
                'Karnataka': (None, None), 'Andhra Pradesh': (None, None), 'Punjab': (None, None),
                'Haryana': (None, None), 'Maharashtra': (None, None), 'Kerala': (None, None),

            }
            # --- *** END OF EXPANDED Dictionary *** ---

            # Map coordinates - Ensure city name from data matches a key in the dict
            # Use .strip() to handle potential whitespace
            location_counts['latitude'] = location_counts['city'].map(lambda x: city_to_lat_lon.get(str(x).strip(), (None, None))[0])
            location_counts['longitude'] = location_counts['city'].map(lambda x: city_to_lat_lon.get(str(x).strip(), (None, None))[1])


            # Log cities that *still* couldn't be mapped (should be fewer now)
            unmapped_cities = location_counts[location_counts['latitude'].isna()]['city'].unique()
            if len(unmapped_cities) > 0:
                 logging.warning(f"Cities still not mapped to coordinates: {', '.join(unmapped_cities)}")

            # Remove rows where coordinates are missing
            map_data = location_counts.dropna(subset=['latitude', 'longitude']).copy()
            logging.info(f"Number of locations with valid coordinates for map: {len(map_data)}")
            logging.info(f"Top 10 locations in final map_data:\n{map_data.sort_values('count', ascending=False).head(10)}")

            if not map_data.empty:
                # Plotting Logic
                fig_map = px.scatter_geo(
                    map_data,
                    lat='latitude', lon='longitude', size='count', color='count',
                    hover_name='city', hover_data={'latitude': False, 'longitude': False, 'count': True},
                    title='Job Postings by Location (Filtered)',
                    color_continuous_scale='Reds', # Reds, Blues, Viridis, Plasma
                    projection='natural earth', scope='asia', center=dict(lat=20.5937, lon=78.9629),
                    size_max=50 # Adjust as needed (e.g., 30, 70)
                )
                fig_map.update_geos(
                    lataxis_range=[5, 37], lonaxis_range=[68, 98],
                    showcoastlines=True, showland=True, landcolor="lightgray",
                    showocean=True, oceancolor="lightblue"
                )
                fig_map.update_layout(height=400, margin={"r":0,"t":25,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.write("Not enough valid location data with coordinates to display map for the selected filters.")
                logging.warning("Map data is empty after removing locations without coordinates.")

    elif 'city' not in jobs_df_filtered.columns:
         st.markdown("<p class='neutral-feedback'>Location insights not available (missing 'city' column).</p>", unsafe_allow_html=True)
         logging.warning("Location insights skipped: 'city' column missing in filtered data.")
    else: # If jobs_df_filtered is empty
         st.markdown("<p class='neutral-feedback'>No location data available for the selected filters.</p>", unsafe_allow_html=True)
         logging.info("Location insights skipped: Filtered DataFrame is empty.")


    # ... (Keep Company Reputation, Job Status Trends, Salary Analysis, Heatmap, Job Listings Table, Footer AS IS) ...
    # ... COMPANY REPUTATION ...
    st.markdown("## ⭐ Company Reputation")
    # ... (reputation code) ...
    if not jobs_df_filtered.empty and 'company' in jobs_df_filtered.columns and 'rating' in jobs_df_filtered.columns:
        col1_rep, col2_rep = st.columns(2)
        with col1_rep:
            # ... (rating bar chart) ...
             company_ratings = jobs_df_filtered[jobs_df_filtered['rating'] > 0].groupby('company')['rating'].mean().reset_index()
             company_ratings = company_ratings.sort_values('rating', ascending=False).head(10)
             if not company_ratings.empty:
                fig_ratings = px.bar(
                    company_ratings, x='rating', y='company', title='Top 10 Companies by Rating (Filtered)',
                    labels={'rating': 'Average Rating', 'company': 'Company'}, orientation='h',
                    color='rating', color_continuous_scale='YlOrRd'
                )
                fig_ratings.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_ratings, use_container_width=True)
             else: st.write("No rated companies found in filtered results.")

        with col2_rep:
            # ... (rating vs reviews scatter) ...
            if 'reviews_count' in jobs_df_filtered.columns:
                scatter_data = jobs_df_filtered.dropna(subset=['rating', 'reviews_count']).copy()
                scatter_data = scatter_data[(scatter_data['rating'] > 0) & (scatter_data['reviews_count'] > 0)]
                if not scatter_data.empty:
                    quantile_cutoff = scatter_data['reviews_count'].quantile(0.98)
                    scatter_data = scatter_data[scatter_data['reviews_count'] <= quantile_cutoff]
                if not scatter_data.empty:
                    scatter_data_display = scatter_data[['company', 'rating', 'reviews_count']]
                    fig_scatter = px.scatter(
                        scatter_data_display, x='reviews_count', y='rating',
                        title='Rating vs. Reviews Count (Filtered)',
                        labels={'rating': 'Rating', 'reviews_count': 'Number of Reviews'},
                        color='rating', color_continuous_scale='YlOrRd',
                        hover_name='company', size='reviews_count', size_max=40
                    )
                    fig_scatter.update_layout(height=400)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else: st.write("Not enough data for rating vs. reviews scatter plot in filtered results.")
            else: st.write("Scatter plot requires 'reviews_count' column.")
    elif 'company' not in jobs_df_filtered.columns or 'rating' not in jobs_df_filtered.columns:
         st.markdown("<p class='neutral-feedback'>Reputation insights require 'company' and 'rating' columns.</p>", unsafe_allow_html=True)
    else: # If jobs_df_filtered is empty
         st.markdown("<p class='neutral-feedback'>No reputation data available for the selected filters.</p>", unsafe_allow_html=True)


    # ... JOB STATUS TRENDS ...
    st.markdown("## 📑 Job Status Trends")
    # ... (status trends code) ...
    if not jobs_df_filtered.empty and 'is_expired' in jobs_df_filtered.columns and 'posting_date' in jobs_df_filtered.columns and pd.api.types.is_datetime64_any_dtype(jobs_df_filtered['posting_date']):
        try:
            status_trends = jobs_df_filtered.groupby(jobs_df_filtered['posting_date'].dt.date)['is_expired'].value_counts().unstack(fill_value=0).reset_index()
            status_trends.rename(columns={False: 'Active', True: 'Expired', 'posting_date': 'date'}, inplace=True) # Rename directly
            if 'Active' not in status_trends.columns: status_trends['Active'] = 0
            if 'Expired' not in status_trends.columns: status_trends['Expired'] = 0

            status_melt = pd.melt(status_trends, id_vars='date', value_vars=['Active', 'Expired'], var_name='Status', value_name='Count')

            fig_status = px.line(
                status_melt, x='date', y='Count', color='Status',
                title='Active vs. Expired Jobs Over Time (Filtered)',
                labels={'date': 'Posting Date', 'Count': 'Number of Jobs', 'Status': 'Job Status'},
                markers=True, color_discrete_map={'Active': '#2ecc71', 'Expired': '#e74c3c'}
            )
            fig_status.update_layout(height=400)
            st.plotly_chart(fig_status, use_container_width=True)
        except Exception as status_trend_error: st.error(f"Could not generate status trends chart: {status_trend_error}")
    elif 'is_expired' not in jobs_df_filtered.columns or 'posting_date' not in jobs_df_filtered.columns:
        st.markdown("<p class='neutral-feedback'>Status trends require 'is_expired' and 'posting_date' columns.</p>", unsafe_allow_html=True)
    else: # If jobs_df_filtered is empty
        st.markdown("<p class='neutral-feedback'>No job status data available for the selected filters.</p>", unsafe_allow_html=True)


    # ... SALARY ANALYSIS ...
    st.markdown("## 💰 Salary Analysis")
    # ... (salary code) ...
    # Helper function (keep as is)
    def extract_salary(salary_text):
        # ... (salary extraction function code) ...
        if pd.isna(salary_text) or not isinstance(salary_text, str): return None, None
        salary_text = salary_text.lower().replace(",", "").replace("₹", "").replace("$", "").replace("£", "").replace("€", "")
        numbers = []
        matches = re.findall(r"(\d+\.?\d*)\s*(k|lakh|lac|crore)?", salary_text)
        if not matches: return None, None
        try:
            for num_str, unit in matches:
                num = float(num_str)
                if unit == "k": num *= 1000
                elif unit in ["lakh", "lac"]: num *= 100000
                elif unit == "crore": num *= 10000000
                numbers.append(num)
            if not numbers: return None, None
            min_salary = numbers[0]
            max_salary = numbers[-1] if len(numbers) > 1 else numbers[0]
            if max_salary < min_salary: min_salary, max_salary = max_salary, min_salary
            return min_salary, max_salary
        except ValueError: return None, None

    # Process salary only if 'salary' column exists
    if 'salary' in jobs_df.columns:
        if not jobs_df_filtered.empty:
            jobs_df_filtered[['min_salary','max_salary']] = jobs_df_filtered['salary'].apply(lambda x: pd.Series(extract_salary(x)))
            salary_df = jobs_df_filtered.dropna(subset=['min_salary']).copy()
        else: salary_df = pd.DataFrame()

        if not salary_df.empty:
            col1_sal, col2_sal, col3_sal = st.columns(3)
            # ... (salary charts) ...
            with col1_sal:
                fig_salary_dist = px.histogram(
                    salary_df, x='min_salary', title='Min Salary Distribution (Filtered)',
                    labels={'min_salary': 'Minimum Salary (Est.)', 'count': 'Jobs'}, nbins=30, color_discrete_sequence=['#6B5B95']
                )
                fig_salary_dist.update_layout(height=400)
                st.plotly_chart(fig_salary_dist, use_container_width=True)
            with col2_sal:
                if 'base_position' in salary_df.columns:
                    avg_salary_by_title = salary_df.groupby('base_position')['min_salary'].mean().sort_values(ascending=False).head(10).reset_index()
                    if not avg_salary_by_title.empty:
                        fig_avg_salary_title = px.bar(
                            avg_salary_by_title, x='min_salary', y='base_position', title='Avg Min Salary by Title (Top 10, Filtered)',
                            labels={'min_salary': 'Avg Min Salary', 'base_position': 'Job Title'}, orientation='h',
                            color='min_salary', color_continuous_scale='Viridis'
                        )
                        fig_avg_salary_title.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_avg_salary_title, use_container_width=True)
                    else: st.write("No salary data by title.")
                else: st.write("Requires 'base_position' column.")
            with col3_sal:
                if 'city' in salary_df.columns:
                    avg_salary_by_location = salary_df.groupby('city')['min_salary'].mean().sort_values(ascending=False).head(10).reset_index()
                    if not avg_salary_by_location.empty:
                        fig_avg_salary_location = px.bar(
                            avg_salary_by_location, x='min_salary', y='city', title='Avg Min Salary by Location (Top 10, Filtered)',
                            labels={'min_salary': 'Avg Min Salary', 'city': 'City'}, orientation='h',
                            color='min_salary', color_continuous_scale='Cividis'
                        )
                        fig_avg_salary_location.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_avg_salary_location, use_container_width=True)
                    else: st.write("No salary data by location.")
                else: st.write("Requires 'city' column.")

            # ... (salary box plot) ...
            st.markdown("### Salary Distribution by Company (Filtered)")
            if 'company' in salary_df.columns:
                top_companies_salary = salary_df['company'].value_counts().head(12).index
                salary_by_company = salary_df[salary_df['company'].isin(top_companies_salary)]
                if not salary_by_company.empty:
                    fig_salary_box = px.box(
                        salary_by_company, x='company', y='min_salary',
                        title=f'Min Salary Distribution (Top {len(top_companies_salary)} Companies, Filtered)',
                        labels={'min_salary': 'Minimum Salary', 'company': 'Company'},
                        color='company', points="outliers"
                    )
                    fig_salary_box.update_layout(height=450, xaxis={'categoryorder':'median descending'})
                    st.plotly_chart(fig_salary_box, use_container_width=True)
                else: st.write("Not enough data for company salary box plot.")
            else: st.write("Requires 'company' column.")

        else: # If salary_df is empty after parsing/filtering
            st.markdown("<p class='neutral-feedback'>No salary data available for the selected filters after parsing.</p>", unsafe_allow_html=True)
    else: # If 'salary' column was missing initially
        st.markdown("<p class='neutral-feedback'>Salary analysis not available (missing 'salary' column in source data).</p>", unsafe_allow_html=True)

    # ... HEATMAP ...
    st.markdown("## 🔥 Posting Frequency by Company (Filtered)")
    # ... (heatmap code) ...
    if not jobs_df_filtered.empty and 'company' in jobs_df_filtered.columns and 'posting_date' in jobs_df_filtered.columns and pd.api.types.is_datetime64_any_dtype(jobs_df_filtered['posting_date']):
        top_n_companies = jobs_df_filtered['company'].value_counts().head(10).index
        heatmap_df = jobs_df_filtered[jobs_df_filtered['company'].isin(top_n_companies)].copy()
        if not heatmap_df.empty:
            heatmap_df.loc[:, 'day_of_week'] = heatmap_df['posting_date'].dt.day_name()
            try:
                heatmap_data = heatmap_df.pivot_table(
                    index='company', columns='day_of_week', values='job_id',
                    aggfunc='count', fill_value=0
                )
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heatmap_data = heatmap_data.reindex(columns=days_order, fill_value=0)

                if not heatmap_data.empty:
                    fig_heatmap = px.imshow(
                        heatmap_data, labels=dict(x="Day of Week", y="Company", color="Job Postings"),
                        x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale='Viridis',
                        aspect="auto", title=f"Posting Frequency (Top {len(top_n_companies)} Companies, Filtered)"
                    )
                    fig_heatmap.update_layout(height=500, xaxis_nticks=7)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                else: st.write("No data for heatmap after pivoting.")
            except Exception as heatmap_error: st.error(f"Could not generate heatmap: {heatmap_error}")
        else: st.write("No data for top companies in filtered results.")
    elif 'company' not in jobs_df_filtered.columns or 'posting_date' not in jobs_df_filtered.columns:
         st.markdown("<p class='neutral-feedback'>Heatmap requires 'company' and 'posting_date' columns.</p>", unsafe_allow_html=True)
    else: # If jobs_df_filtered is empty
         st.markdown("<p class='neutral-feedback'>No frequency data available for the selected filters.</p>", unsafe_allow_html=True)

    # ... JOB LISTINGS TABLE ...
    st.markdown("## 📋 Job Listings (Filtered)")
    # ... (table code) ...
    search_term = st.text_input("Search within filtered jobs by keyword (title, company, location)", "", key="table_search")
    search_df = jobs_df_filtered.copy() # Start with the fully filtered df
    if search_term:
        search_df = search_df.loc[
            search_df['position'].astype(str).str.contains(search_term, case=False, na=False) |
            search_df['company'].astype(str).str.contains(search_term, case=False, na=False) |
            search_df['location'].astype(str).str.contains(search_term, case=False, na=False)
        ]

    items_per_page = 15
    total_rows = len(search_df)
    total_pages = max(1, (total_rows - 1) // items_per_page + 1) if total_rows > 0 else 0
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="table_page", disabled=(total_pages==0))

    if total_rows > 0:
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_rows)
        paginated_df = search_df.iloc[start_idx:end_idx].copy()

        display_cols_order = ['position', 'company', 'city', 'salary', 'rating', 'posting_date', 'status', 'Link']
        display_df = pd.DataFrame() # Initialize empty df

        # Create display columns safely
        if 'position' in paginated_df: display_df['position'] = paginated_df['position']
        if 'company' in paginated_df: display_df['company'] = paginated_df['company']
        if 'city' in paginated_df: display_df['city'] = paginated_df['city']
        if 'salary' in paginated_df: display_df['salary'] = paginated_df['salary'].fillna('N/A')
        if 'rating' in paginated_df: display_df['rating'] = paginated_df['rating'].apply(lambda x: f"{x:.1f} ⭐" if pd.notna(x) and x > 0 else 'N/A')
        if 'posting_date' in paginated_df: display_df['posting_date'] = pd.to_datetime(paginated_df['posting_date']).dt.strftime('%Y-%m-%d')
        if 'is_expired' in paginated_df: display_df['status'] = paginated_df['is_expired'].apply(lambda x: "Expired" if x else "Active")
        else: display_df['status'] = 'N/A' # If is_expired column missing
        if 'job_url' in paginated_df: display_df['Link'] = paginated_df['job_url'].apply(lambda x: f'<a href="{x}" target="_blank">View</a>' if pd.notna(x) else 'N/A')
        else: display_df['Link'] = 'N/A'

        # Ensure all columns in display_cols_order exist before reindexing
        final_display_cols = [col for col in display_cols_order if col in display_df.columns]
        display_df = display_df[final_display_cols]

        st.write(f"Showing {start_idx+1}-{end_idx} of {total_rows} jobs")
        st.markdown(display_df.to_html(escape=False, index=False, classes='dataframe small-table', justify='left'), unsafe_allow_html=True)
        st.markdown("""<style>.small-table th, .small-table td { padding: 0.3rem 0.5rem; font-size: 0.9em; text-align: left; } .small-table th { font-weight: bold; }</style>""", unsafe_allow_html=True)
    else:
        st.write("No jobs found matching your criteria.")


    # --- FOOTER ---
    st.markdown("---")
    # ... (footer code) ...
    last_updated_time = jobs_df['scraped_at'].max().strftime("%Y-%m-%d %H:%M") if 'scraped_at' in jobs_df.columns and not jobs_df.empty else datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"Job Market Insights Dashboard | Data via Supabase | Last data scraped: {last_updated_time}")


# --- End of show_dashboard() ---