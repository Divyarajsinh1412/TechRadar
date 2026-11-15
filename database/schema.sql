-- TechRadar SQLite Schema
-- Multi-Period (Daily, Weekly, Monthly) Technology Intelligence Database

CREATE TABLE IF NOT EXISTS technology_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS technologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category_id INTEGER,
    category_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES technology_categories(id)
);

CREATE TABLE IF NOT EXISTS technology_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technology TEXT NOT NULL,
    category TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    date TEXT NOT NULL,
    job_postings INTEGER DEFAULT 0,
    developer_interest REAL,
    company_adoption REAL,
    average_salary REAL,
    github_activity REAL,
    skill_demand REAL,
    growth_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Multi-Period Live Observations Table
CREATE TABLE IF NOT EXISTS live_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_date TEXT NOT NULL,
    technology TEXT NOT NULL,
    category TEXT NOT NULL,
    source_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    data_frequency TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'
    data_quality_status TEXT NOT NULL, -- 'verified_live', 'cached_benchmark', 'rate_limited'
    source_url TEXT,
    collection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(observation_date, technology, source_id, metric_name, data_frequency)
);

-- Data Source Status Tracking Table
CREATE TABLE IF NOT EXISTS data_source_status (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    last_refresh TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL, -- 'active', 'rate_limited', 'offline_cached', 'periodic_benchmark'
    available_frequency TEXT NOT NULL, -- 'Daily', 'Weekly', 'Monthly', 'Annual Benchmark'
    records_count INTEGER DEFAULT 0,
    message TEXT
);

CREATE TABLE IF NOT EXISTS uploaded_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- Automated Collection History Table
CREATE TABLE IF NOT EXISTS collection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL, -- 'success', 'partial', 'failed', 'rate_limited'
    records_collected INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT
);

-- Raw Job Postings Deduplication Table
CREATE TABLE IF NOT EXISTS raw_job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    source_id TEXT NOT NULL DEFAULT 'adzuna',
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    country TEXT DEFAULT 'in',
    salary_min REAL,
    salary_max REAL,
    detected_skills TEXT,
    posting_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_tech ON technology_metrics(technology);
CREATE INDEX IF NOT EXISTS idx_metrics_cat ON technology_metrics(category);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON technology_metrics(date);
CREATE INDEX IF NOT EXISTS idx_metrics_year_month ON technology_metrics(year, month);

CREATE INDEX IF NOT EXISTS idx_live_obs_date ON live_observations(observation_date);
CREATE INDEX IF NOT EXISTS idx_live_obs_tech ON live_observations(technology);
CREATE INDEX IF NOT EXISTS idx_live_obs_freq ON live_observations(data_frequency);
CREATE INDEX IF NOT EXISTS idx_live_obs_source ON live_observations(source_id);
CREATE INDEX IF NOT EXISTS idx_collection_hist_source ON collection_history(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_date ON raw_job_postings(posting_date);
