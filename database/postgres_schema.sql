-- ====================================================================
-- TechRadar — Supabase PostgreSQL Production Schema
-- Compatible with Supabase PostgreSQL 15+ and SQLAlchemy 2.0
-- ====================================================================

-- 1. Technologies Master Table
CREATE TABLE IF NOT EXISTS technologies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    website VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories Master Table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Historical Technology Metrics Table (Longitudinal Benchmark)
CREATE TABLE IF NOT EXISTS technology_metrics (
    id SERIAL PRIMARY KEY,
    technology VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    date VARCHAR(20) NOT NULL,
    job_postings INTEGER NOT NULL,
    developer_interest DOUBLE PRECISION,
    company_adoption DOUBLE PRECISION,
    average_salary DOUBLE PRECISION,
    github_activity DOUBLE PRECISION,
    skill_demand DOUBLE PRECISION,
    growth_rate DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tech_metrics_date UNIQUE (technology, date)
);

-- 4. Unified Live Observations Table (Multi-Frequency: Daily, Weekly, Monthly)
CREATE TABLE IF NOT EXISTS live_observations (
    id SERIAL PRIMARY KEY,
    observation_date VARCHAR(20) NOT NULL,
    technology VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL, -- 'github', 'huggingface', 'adzuna', 'google_trends', 'developer_survey'
    metric_name VARCHAR(100) NOT NULL, -- 'stars', 'forks', 'downloads', 'likes', 'job_postings', 'search_interest', etc.
    metric_value DOUBLE PRECISION NOT NULL,
    data_frequency VARCHAR(20) NOT NULL DEFAULT 'daily', -- 'daily', 'weekly', 'monthly'
    data_quality_status VARCHAR(50) NOT NULL DEFAULT 'verified_live', -- 'verified_live', 'cached_benchmark', 'rate_limited'
    source_url TEXT,
    raw_metadata JSONB,
    collection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_live_obs UNIQUE (observation_date, technology, source_id, metric_name, data_frequency)
);

-- 5. Data Source Operational Status Table
CREATE TABLE IF NOT EXISTS data_source_status (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    last_refresh TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- 'active', 'rate_limited', 'offline_cached', 'periodic_benchmark', 'error'
    available_frequency VARCHAR(50) NOT NULL, -- 'Daily', 'Weekly', 'Monthly', 'Annual Benchmark'
    records_count INTEGER DEFAULT 0,
    message TEXT
);

-- 6. User Uploaded Datasets Table
CREATE TABLE IF NOT EXISTS uploaded_datasets (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- 7. Automated Collection Job History Table
CREATE TABLE IF NOT EXISTS collection_history (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL,
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'success', 'partial', 'failed', 'rate_limited'
    records_collected INTEGER DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- 8. Raw Job Postings Table (Adzuna / CSV deduplication)
CREATE TABLE IF NOT EXISTS raw_job_postings (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    source_id VARCHAR(50) NOT NULL DEFAULT 'adzuna',
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    location VARCHAR(255),
    country VARCHAR(10) DEFAULT 'in',
    salary_min DOUBLE PRECISION,
    salary_max DOUBLE PRECISION,
    detected_skills TEXT, -- Comma-separated list of technologies detected
    posting_date VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- Performance Indexes for Analytics & Dashboard Queries
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_pg_metrics_tech ON technology_metrics(technology);
CREATE INDEX IF NOT EXISTS idx_pg_metrics_cat ON technology_metrics(category);
CREATE INDEX IF NOT EXISTS idx_pg_metrics_date ON technology_metrics(date);
CREATE INDEX IF NOT EXISTS idx_pg_metrics_year_month ON technology_metrics(year, month);

CREATE INDEX IF NOT EXISTS idx_pg_live_obs_date ON live_observations(observation_date);
CREATE INDEX IF NOT EXISTS idx_pg_live_obs_tech ON live_observations(technology);
CREATE INDEX IF NOT EXISTS idx_pg_live_obs_freq ON live_observations(data_frequency);
CREATE INDEX IF NOT EXISTS idx_pg_live_obs_source ON live_observations(source_id);
CREATE INDEX IF NOT EXISTS idx_pg_live_obs_composite ON live_observations(technology, observation_date, data_frequency);

CREATE INDEX IF NOT EXISTS idx_pg_raw_jobs_date ON raw_job_postings(posting_date);
CREATE INDEX IF NOT EXISTS idx_pg_raw_jobs_company ON raw_job_postings(company);
CREATE INDEX IF NOT EXISTS idx_pg_collection_hist_source ON collection_history(source_id, start_time DESC);
