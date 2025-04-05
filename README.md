# Pathlight AI - Career Suite

![Pathlight AI](https://img.shields.io/badge/Pathlight-AI-3498db)
![Version](https://img.shields.io/badge/Version-1.3-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43.2-red)
![Google Gemini](https://img.shields.io/badge/Google-Gemini-yellow)

## Overview

Pathlight AI is a comprehensive career advancement platform that leverages Google's Gemini AI models to help job seekers optimize their application materials and career strategy. The platform provides detailed resume analysis, career tools, and job market insights through an intuitive web interface built with Streamlit.

## Features

### 📄 Resume Analysis & Tools

- **Standard Analysis**: 
  - Compares your resume against job descriptions with a hybrid matching algorithm
  - Combines keyword matching and semantic similarity for accurate assessment
  - Provides detailed feedback on technical skills, soft skills, experience, and education
  - Highlights strengths and identifies gaps with actionable suggestions

- **ATS Optimization**: 
  - Evaluates resume compatibility with Applicant Tracking Systems
  - Checks spelling, grammar, and formatting issues
  - Identifies passive voice and suggests active alternatives
  - Detects repeated words and suggests variations
  - Analyzes bullet point length and impact
  - Provides structure and formatting recommendations
  - Ensures contact information is complete and properly formatted

- **Cover Letter Synthesizer**: 
  - Creates highly personalized cover letters based on both resume and job description
  - Maintains professional tone while sounding natural and human-written
  - Structures content according to professional standards
  - Integrates relevant achievements and skills from your resume
  - Connects your experience to job requirements
  - Automatically formats with your contact information

- **LinkedIn Optimization**: 
  - Provides detailed headline suggestions with rationale
  - Offers structured "About" section content
  - Optimizes experience descriptions to highlight achievements
  - Recommends skills to add and prioritize for endorsements
  - Suggests additional sections (Projects, Certifications)
  - Includes overall profile tips for maximum visibility

- **Interview Tips**: 
  - Generates hyper-personalized interview preparation strategies
  - Creates potential behavioral questions with STAR method response frameworks
  - Develops technical questions based on job requirements and your experience
  - Identifies focus areas based on resume-job description gap analysis
  - Provides questions you should ask the interviewer
  - Links all suggestions directly to your resume and the job description

- **Career Roadmap**: 
  - Develops a comprehensive career progression path
  - Divides goals into short-term (1-2 years), mid-term (3-5 years), and long-term (5+ years)
  - Recommends specific skills, certifications, and projects
  - Includes resources with valid URLs for each recommendation
  - Provides detailed justification based on your current skills and experience

### 🎯 Job Recommendations

- Analyzes your resume or skills description to suggest optimal job roles
- Provides detailed justification for recommended roles
- Creates a structured career development roadmap with specific goals and timelines
- Recommends relevant certifications with detailed descriptions
- Suggests project ideas at beginner, intermediate, and advanced levels
- Lists key technologies and skills to develop with specific descriptions

### 📊 Job Market Insights

- Interactive dashboard for the Indian job market with real-time data
- Comprehensive filtering by company, job title, location, and date range
- Visualizations for salary trends, job distribution, and market demand
- Analytics for job freshness and position availability
- Company-specific metrics and comparisons

## Technology Stack & Architecture

### Core Components

- **Frontend**: Streamlit web application with custom CSS for enhanced UI/UX
- **AI Integration**: Google Generative AI (Gemini models) with configurable model selection
- **NLP Processing**: 
  - Spacy for text analysis and keyword extraction
  - Sentence Transformers for semantic similarity
  - FAISS for efficient vector search and matching
- **Document Processing**: PyPDF2 and python-docx for resume parsing
- **Data Visualization**: Plotly and Matplotlib for interactive charts
- **Database**: Supabase for job market data storage and retrieval
- **Data Analysis**: Pandas for structured data manipulation

### Architectural Design

The application follows a modular architecture with clear separation of concerns:

```
├── main.py                 # Application entry point and orchestration
├── analysis.py             # Core resume analysis engine
├── ats_optimization.py     # ATS-specific analysis and recommendations
├── cover_letter.py         # Cover letter generation logic
├── linkedin_optimization.py # LinkedIn profile enhancement
├── interview_tips.py       # Interview preparation system
├── career_roadmap.py       # Career progression planning
├── job_recommendation.py   # Job role suggestions
├── dashboard.py            # Job market visualization and analytics
├── display.py              # UI components and styling
└── utils.py                # Shared utility functions
```

### AI Prompt Engineering

The project employs sophisticated prompt engineering techniques:

- **Structured JSON Output**: All AI prompts are designed to generate structured JSON responses for consistent parsing
- **Explicit Instructions**: Clear and detailed directives ensure high-quality, focused outputs
- **Format Specification**: Each prompt includes detailed JSON schema specifications
- **Error Handling**: Robust response parsing with error recovery and retry mechanisms
- **Context Integration**: Dynamic inclusion of user inputs (resume, job descriptions) with clear separators

## Technical Implementation Details

### Resume Analysis Engine

The application employs a hybrid matching approach that combines:

1. **Keyword Matching**:
   - Extracts keywords from job descriptions using Spacy
   - Expands keywords with relevant synonyms
   - Identifies presence in resume text
   - Calculates match percentage

2. **Semantic Similarity**:
   - Generates embeddings using Sentence Transformers
   - Creates FAISS indices for efficient vector search
   - Calculates normalized similarity scores
   - Combines with keyword scores for hybrid matching

3. **Gap Analysis**:
   - Identifies missing skills and experience
   - Provides justification for why these are important
   - Offers actionable remediation suggestions
   - Links to relevant learning resources

### ATS Optimization System

The ATS checker performs multiple analyses:

1. **Document Structure**:
   - Verifies essential sections (education, experience, skills)
   - Checks section ordering and prominence
   - Analyzes overall layout and formatting

2. **Content Quality**:
   - Evaluates spelling and grammar
   - Detects passive voice constructions
   - Identifies overused words and phrases
   - Assesses bullet point effectiveness
   - Checks for quantified achievements

3. **Technical Compatibility**:
   - Measures text extraction success rate
   - Evaluates PDF structure for parsing issues
   - Checks for font embedding and accessibility

### Job Market Analytics

The dashboard functionality includes:

1. **Data Processing**:
   - Cleans and normalizes job data from Supabase
   - Extracts cities from location strings
   - Standardizes job titles for meaningful aggregation
   - Calculates job freshness metrics

2. **Visualization**:
   - Interactive charts for market trends
   - Geospatial distribution of opportunities
   - Salary comparisons across roles and locations
   - Company-specific analytics

3. **Filtering System**:
   - Multi-select filters for companies and positions
   - Date range selection with dynamic adaptation
   - Status filtering (active vs. expired)
   - Location-based filtering

## Error Handling & Resilience

The application implements comprehensive error handling:

- **AI Service Errors**: Catch and process API-specific exceptions
- **Retry Logic**: Automatic retries for transient failures
- **Fallback Mechanisms**: Default values and graceful degradation
- **User Feedback**: Clear error messages with suggested actions
- **Logging**: Detailed logging throughout for diagnostics and monitoring

## Setup and Configuration

### Prerequisites

1. **Python Environment**:
   - Python 3.8 or higher
   - Virtual environment recommended

2. **API Keys**:
   - Google Gemini API key
   - Supabase credentials (URL and key)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pathlight-ai.git
   cd pathlight-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Create a `.streamlit/secrets.toml` file with:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_key"
   ```

5. Download required models:
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Running the Application

Start the Streamlit application:
```bash
streamlit run main.py
```

## Usage Guide

### Resume Analysis

1. Navigate to the "Resume Analysis & Tools" tab
2. Upload your resume (PDF or DOCX format)
3. Select an analysis type from the sidebar
4. For comparison tools, paste a job description
5. Click "Run [Selected Tool]"
6. Review the analysis and download any outputs

### Job Recommendations

1. Navigate to the "Job Recommendations" tab
2. Choose between pasting text or uploading your resume
3. Provide details about your skills and experience
4. Click "Get Job Recommendation & Roadmap"
5. Review the personalized role suggestions and development plan

### Job Market Insights

1. Navigate to the "Job Market Insights" tab
2. Use the sidebar filters to refine the dashboard view
3. Explore the interactive visualizations
4. Analyze trends, salary data, and company comparisons

## Performance Optimization

The application includes several performance optimizations:

- **Caching**: Streamlit's cache mechanisms for model loading and data fetching
- **Lazy Loading**: Components load only when needed
- **Efficient Vector Search**: FAISS for high-performance similarity matching
- **Response Parsing**: Robust JSON extraction for reliable AI outputs
- **Session State Management**: Persistent state for improved user experience

## Privacy and Security

- **Local Processing**: Resume parsing performed locally
- **No Data Storage**: User resumes and job descriptions are not stored
- **API Key Protection**: Secure handling of API keys via Streamlit secrets
- **Error Sanitization**: Detailed errors logged but sanitized for user display

## Future Development Roadmap

Potential enhancements for future releases:

1. **Advanced Analytics**:
   - Predictive salary modeling
   - Skills demand forecasting
   - Career path optimization

2. **Enhanced AI Features**:
   - Video interview preparation
   - Personalized learning path generation
   - Networking strategy optimization

3. **Platform Extensions**:
   - Mobile application
   - Chrome extension for job application assistance
   - Email integration for application tracking

4. **Infrastructure**:
   - Multi-model AI support
   - Enhanced caching for faster performance
   - Distributed processing for large-scale analysis

---

## Contributors

- **Lead Developer**: [Gagan N](https://www.linkedin.com/in/gagan-rao)

## License

This project is proprietary software. All rights reserved.

---

Created with ❤️ using Google Gemini AI 
