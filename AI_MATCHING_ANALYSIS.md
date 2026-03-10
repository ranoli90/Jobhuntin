# AI Job Matching System Analysis

## Overview
The system uses a sophisticated multi-dimensional AI matching system to intelligently filter and score jobs for users.

## Matching Components

### 1. **Semantic Matching (30% weight)**
- Uses vector embeddings (cosine similarity) to match job descriptions with candidate profiles
- Embeds both profile and job text into high-dimensional vectors
- Computes semantic similarity score
- **Caching**: Embeddings are cached in database to avoid recomputation
- **Efficiency**: Reuses cached embeddings when profile/job hasn't changed

### 2. **Skill Matching (25% weight)**
- Extracts skills from both profile and job description
- Matches skills with confidence weighting (high/medium/low confidence)
- Computes skill match ratio: matched_skills / (matched_skills + missing_skills)
- **Intelligence**: Uses rich skills format with confidence scores for better matching

### 3. **Experience Alignment (15% weight)**
- Compares user's years of experience with job requirements
- Analyzes experience level alignment (junior/mid/senior)
- **Smart**: Considers both explicit years and implicit experience indicators

### 4. **Work Style Fit (18% weight)**
- Matches user's work style preferences with company culture
- Considers: autonomy, learning style, company stage, communication style, pace, ownership, career trajectory
- **Personalization**: Uses work_style_profiles table for precise matching

### 5. **Trajectory Alignment (12% weight)**
- Aligns user's career goals with job's growth potential
- Matches career trajectory preferences
- **Future-focused**: Considers long-term fit, not just current skills

## Dealbreaker Filters

The system applies strict filters before scoring:
- **Salary**: Filters jobs outside min/max salary range
- **Location**: Respects remote_only, onsite_only, or specific locations
- **Visa**: Filters based on visa sponsorship requirements
- **Excluded Companies**: Removes blacklisted companies
- **Excluded Keywords**: Filters jobs with unwanted keywords

## Resume Tailoring

### Per-Job Customization
- **Tailored Summary**: LLM generates job-specific professional summary
- **Skill Prioritization**: Reorders skills to highlight most relevant ones
- **Experience Emphasis**: Prioritizes relevant work experiences
- **Keyword Optimization**: Adds missing keywords from job description
- **ATS Score**: Computes ATS optimization score (0-1) for each tailored resume

### Efficiency
- **On-Demand**: Tailoring happens when user applies (not pre-computed)
- **Caching**: Tailored resumes can be cached per job
- **Fast**: Uses efficient LLM calls with optimized prompts

## Pre-Computation System

### Match Score Pre-Computation
- Background job pre-computes match scores for active users and jobs
- Stores scores in `match_scores` table for fast retrieval
- **Batch Processing**: Processes in batches of 50 jobs
- **Rate Limiting**: Small delays between computations to avoid overload
- **Smart Selection**: Only processes users with completed onboarding and active jobs

## Job Search Flow

1. **Query Building**: Constructs SQL query with filters (location, salary, keywords, etc.)
2. **Database Fetch**: Retrieves jobs from database
3. **Deduplication**: Removes duplicate jobs using normalization
4. **Profile Assembly**: Assembles user profile from multiple sources
5. **Dealbreaker Filtering**: Removes jobs that violate dealbreakers
6. **Match Scoring**: Computes match scores for remaining jobs
7. **Sorting**: Sorts by match_score, salary, or date_posted
8. **Pagination**: Returns requested page of results

## Efficiency Optimizations

1. **Embedding Caching**: Profile and job embeddings cached in database
2. **Pre-computed Scores**: Match scores pre-computed in background
3. **Batch Processing**: Processes multiple jobs in batches
4. **Smart Fetching**: Fetches extra jobs to account for dealbreaker filtering
5. **Database Indexing**: Uses indexes on user_id, job_id, is_active, etc.

## Performance Metrics

- **Match Scoring Latency**: Tracked via `job_search.match_scoring_latency_seconds`
- **Jobs Scored**: Counter for number of jobs scored per user
- **Pre-computation Stats**: Tracks users/jobs processed, scores computed, errors

## Application Flow

1. **User Swipes/Applies**: Creates application with job_id and decision (ACCEPT/REJECT)
2. **Resume Tailoring**: System tailors resume for that specific job
3. **Application Creation**: Creates application record in database
4. **Status Tracking**: Tracks application status (QUEUED, PROCESSING, APPLIED, etc.)
5. **Input Handling**: Handles questions/inputs required for application

## Intelligence Features

1. **Multi-Perspective Matching**: Considers semantic, skills, experience, work style, and trajectory
2. **Confidence Weighting**: Uses confidence scores for skills matching
3. **Explainable Scores**: Provides reasoning for each match
4. **Adaptive Filtering**: Applies dealbreakers before scoring to save computation
5. **Personalization**: Uses user's complete profile (skills, preferences, work style, goals)

## Current Status

- ✅ Semantic matching implemented with caching
- ✅ Skill matching with confidence weighting
- ✅ Work style matching
- ✅ Resume tailoring per job
- ✅ Dealbreaker filtering
- ✅ Pre-computation system
- ⚠️ Backend error blocking job search (TypeError in middleware)
- ⚠️ Need to verify jobs exist in database
