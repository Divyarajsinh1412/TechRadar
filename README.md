# TechRadar — Technology Trends & Future Skills Analytics

> **Tagline:** Discover Tomorrow's Technology Skills Today.  
> **Academic Project:** MCA Mini-Project for **CSA4503 Data Analytics and Visualization**  
> **Architecture:** Streamlit SaaS Frontend • Supabase PostgreSQL Cloud Database • Real External API Collectors • Render Deployment

---

## 1. Project Objective

**TechRadar** is a comprehensive, production-grade Python Data Analytics and Visualization web application designed to analyze programming languages, software frameworks, cloud platforms, developer skills, and technology job-market trends.

The application empirically answers:
1. **Which programming languages are gaining popularity?** (e.g., Python, Rust, Go, TypeScript)
2. **Which technologies are accelerating in developer interest?** (e.g., PyTorch, LangChain, Hugging Face, Vite)
3. **Which skills are most demanded by enterprises?** (e.g., AWS, Docker, Kubernetes, PostgreSQL)
4. **Which technologies exhibit high growth despite currently lower adoption?** (e.g., Rust, Zig, FastAPI)
5. **Which technology categories lead the market?** (Cloud & DevOps, AI & Machine Learning, Web Development)
6. **Which technologies are worth prioritizing for students and engineers?** (via explainable multi-criteria Opportunity Scoring)

---

## 2. Cloud Database & Production Architecture

TechRadar supports dual-mode database operation:

* **Production Cloud Database (Supabase PostgreSQL):**
  Connects via SQLAlchemy 2.0 with connection pooling (`QueuePool`, `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`).
  Configured simply by setting the `DATABASE_URL` environment variable.
  Includes relational tables, composite unique keys for zero-duplicate upserts, and B-Tree indexes for fast multi-dimensional analytics.
* **Local Development Fallback (SQLite):**
  When `DATABASE_URL` is not specified, TechRadar automatically falls back to local SQLite storage (`database/techradar.db`), requiring zero manual database configuration for local testing.

### Database Tables:
* `technologies`: Canonical technology master registry.
* `categories`: Technology domain classifications.
* `technology_metrics`: Longitudinal 5-year historical benchmark series.
* `live_observations`: Unified telemetry table storing Daily, Weekly, and Monthly observations across all external collectors with unique constraint on `(observation_date, technology, source_id, metric_name, data_frequency)`.
* `data_source_status`: Live telemetry health and sync timestamps for each source.
* `collection_history`: Execution history, timing, and record counts for scheduled cron jobs.
* `raw_job_postings`: Deduplicated raw hiring posts with detected technology skills.
* `uploaded_datasets`: Metadata tracking for user-uploaded datasets.

---

## 3. Real External API Collectors

Located in the [`collectors/`](file:///d:/TechRadar/collectors/) package:

| Collector | Source & API | Data Collected | Authentication / Env |
|---|---|---|---|
| **GitHub REST API** | `api.github.com/search/repositories` | Stargazer velocity, fork counts, open issues, primary language, repository creation dates, push activity | `GITHUB_TOKEN` (Supports authenticated 5,000 req/hr and polite unauthenticated 60 req/hr fallback) |
| **Hugging Face Hub API** | `huggingface.co/api/models` | AI model ecosystem, total model downloads, community likes, and framework tags (`pytorch`, `transformers`, `diffusers`, `onnx`) | Official public REST API (Zero auth required) |
| **Adzuna Job Market API** | `api.adzuna.com/v1/api/jobs/{country}/search` | Live enterprise job postings, titles, companies, locations, salary ranges, and technology skill extraction | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY` (default: `in` for India) |
| **Real Job Postings CSV Ingest** | Built into Adzuna Collector | Offline alternative: imports Kaggle, LinkedIn, or Indeed job market CSVs, extracts canonical skills, and deduplicates postings | UI File Uploader in Page 2 |
| **Google Trends** | `pytrends.request.TrendReq` | Normalized search-interest trajectories (0–100 relative index; never misinterpreted as absolute volume) | Public Google Trends API (Gracefully catches 429 rate limits) |
| **Developer Surveys** | Stack Overflow & JetBrains | Industry sentiment, admiration, and adoption baseline | Transparently labeled as `periodic_benchmark` |

---

## 4. Automated Scheduled Collection (Render Cron Jobs)

All collectors are unified under [`scripts/run_collector.py`](file:///d:/TechRadar/scripts/run_collector.py), designed for execution via **Render Cron Jobs**:

* **GitHub Collector (Every 6 Hours):**
  ```powershell
  python scripts/run_collector.py --source github
  ```
* **Hugging Face Hub Collector (Every 6 Hours):**
  ```powershell
  python scripts/run_collector.py --source huggingface
  ```
* **Adzuna Job Market Telemetry (Every 12 Hours):**
  ```powershell
  python scripts/run_collector.py --source adzuna
  ```
* **Google Trends Interest (Daily):**
  ```powershell
  python scripts/run_collector.py --source google_trends
  ```
* **Unified Pipeline (All Sources):**
  ```powershell
  python scripts/run_collector.py --source all
  ```

---

## 5. Supabase Database Migration

To migrate existing local SQLite data into Supabase PostgreSQL:

1. Obtain your Supabase PostgreSQL connection string from the Supabase Dashboard:
   `Settings` $\rightarrow$ `Database` $\rightarrow$ `Connection String` (URI).
2. Run the migration script:
   ```powershell
   python scripts/migrate_sqlite_to_pg.py --postgres-url "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
   ```
   Or set `DATABASE_URL` in your `.env` file and execute:
   ```powershell
   python scripts/migrate_sqlite_to_pg.py
   ```
The migration script automatically executes [`database/postgres_schema.sql`](file:///d:/TechRadar/database/postgres_schema.sql), creates all required tables and indexes, maps data types, and safely upserts records without duplication.

---

## 6. Render Cloud Deployment

TechRadar is pre-configured for one-click deployment using **Render Blueprints** via [`render.yaml`](file:///d:/TechRadar/render.yaml):

### Step 1: Push Repository to GitHub
Ensure `.env` is NOT committed (verified by `.gitignore`).

### Step 2: Create a Blueprint Instance on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New** $\rightarrow$ **Blueprint**.
2. Connect your GitHub repository.
3. Render will read `render.yaml` and provision:
   * **`techradar-web`**: Web Service running `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
   * **`techradar-cron-github`**: Cron Job running every 6 hours
   * **`techradar-cron-huggingface`**: Cron Job running every 6 hours
   * **`techradar-cron-jobs`**: Cron Job running every 12 hours
   * **`techradar-cron-google-trends`**: Cron Job running daily

### Step 3: Configure Environment Variables in Render
In the Render Web Service Settings, add the following secrets:
* `DATABASE_URL`: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
* `GITHUB_TOKEN`: `ghp_xxxxxxxxxxxxxxxxxxxx` (Optional, enhances GitHub API rate limits)
* `ADZUNA_APP_ID`: `your_adzuna_app_id`
* `ADZUNA_APP_KEY`: `your_adzuna_app_key`
* `ADZUNA_COUNTRY`: `in`

---

## 7. Project Folder Structure

```
TechRadar/
│
├── app.py                             # PAGE 1: Home Dashboard (Multi-Period Live Intelligence)
├── render.yaml                        # Render Cloud Blueprint (Web service + 4 Cron jobs)
├── Procfile                           # Web process configuration for cloud PaaS
├── requirements.txt                   # Dependency specification with SQLAlchemy & psycopg2
├── .env.example                       # Environment variables template
├── .gitignore                         # Secret protection & bytecode ignoring
├── README.md                          # Comprehensive documentation
│
├── collectors/                        # Real External API Collectors
│   ├── __init__.py
│   ├── base_collector.py              # Base class with retries, logging, and DB persistence
│   ├── github_collector.py            # GitHub REST API repository & star intelligence
│   ├── huggingface_collector.py       # Hugging Face Hub model download & like signals
│   ├── adzuna_collector.py            # Adzuna Job Market API & real CSV skill extractor
│   ├── google_trends_collector.py     # Google Trends normalized search interest
│   └── developer_survey_collector.py  # Periodic developer survey benchmark signals
│
├── scripts/                           # Administrative & Automation Scripts
│   ├── run_collector.py               # CLI & Cron runner for data collectors
│   └── migrate_sqlite_to_pg.py        # SQLite to Supabase PostgreSQL migration script
│
├── database/                          # Relational Storage Engines
│   ├── db.py                          # Dual-engine connection manager (PostgreSQL + SQLite)
│   ├── schema.sql                     # SQLite relational DDL schema
│   ├── postgres_schema.sql            # Supabase PostgreSQL production DDL schema
│   └── techradar.db                   # Local SQLite database file
│
├── data/                              # Data Storage & Historical Baselines
│   ├── sample_technology_data.csv    # 5-year longitudinal baseline (2021–2025, 3,020 records)
│   ├── tech_trends_daily.csv          # 90-day daily observations (4,500 records)
│   └── tech_trends_weekly.csv         # Weekly resampled observations
│
├── modules/                           # Analytics & Visualization Engine
│   ├── data_loader.py                 # Multi-frequency data ingestion and caching
│   ├── multi_period_analytics.py      # Zero-safe growth, moving averages (MA_7, MA_4), live ranking
│   ├── multi_period_generator.py      # Resampling and observation generator
│   ├── live_collector.py              # Offline/online collector dispatcher
│   ├── data_cleaning.py               # Deduplication, imputation, alias normalization, IQR filtering
│   ├── statistical_analysis.py        # Descriptive statistics, correlation matrices (Pearson/Spearman)
│   ├── exploratory_analysis.py        # Profiling, distributions, categorical boxplots
│   ├── time_series.py                 # Datetime indexing, frequency resampling, lags
│   ├── aggregation.py                 # GroupBy, MultiIndex, pivot tables, cross-tabulation
│   ├── opportunity_analysis.py        # Future Opportunity Index (FOI) & Spike Rejection
│   ├── visualization.py               # Matplotlib, Seaborn, and Plotly visual components
│   ├── chart_styles.py                # Unified dark SaaS styling palette
│   ├── ui_components.py               # Responsive header, KPI cards, DB status pills, source chips
│   └── report_generator.py            # Academic PDF report generator via ReportLab
│
├── pages/                             # Multi-Page Streamlit Application
│   ├── 1_Data_Explorer.py             # Data Explorer & File Ingestion
│   ├── 2_Data_Preprocessing.py        # Data Cleaning, IQR Outliers & Real Job CSV Ingestion
│   ├── 3_Exploratory_Analysis.py      # Statistical Profiling & Distributions
│   ├── 4_Visualizations.py            # Comparative Visualizations & Head-to-Head Scorecards
│   ├── 5_Data_Aggregation.py          # GroupBy, MultiIndex & Pivot Tables
│   ├── 6_Time_Series_Analysis.py      # Time Series Resampling & Rolling Windows
│   ├── 7_Future_Technology_Insights.py # Future Opportunity Scoring & Momentum Analytics
│   └── 8_Reports.py                   # Executive PDF & CSV Report Generator
│
├── assets/
│   └── style.css                      # Premium Dark SaaS stylesheet
│
└── tests/                             # Automated Test Suites (30 Tests Total)
    ├── test_analytics.py              # 11 Unit tests covering CSA4503 analytical modules
    ├── test_multi_period.py           # 8 Unit tests covering Daily/Weekly/Monthly calculations
    └── test_collectors.py             # 11 Unit tests covering real collectors, deduplication & DB
```

---

## 8. Academic Course Mapping (CSA4503)

TechRadar directly implements the theoretical and practical concepts taught across all four modules of **CSA4503 Data Analytics and Visualization**:

| Course Module | Syllabus Concepts Covered | TechRadar Implementation |
|---|---|---|
| **Module 1: Introduction to Data Analytics & EDA** | • Data science lifecycle<br/>• Exploratory data analysis (EDA)<br/>• Python data analytics libraries | `pages/1_Data_Explorer.py`<br/>`modules/exploratory_analysis.py`<br/>Structural shape, dtypes, missingness profiling |
| **Module 2: NumPy, Pandas & Data Cleaning** | • Pandas Series & DataFrames<br/>• Descriptive statistics (Mean, Median, Mode, Std, Variance, Skewness, Kurtosis)<br/>• Handling missing data (Mean/Median/Mode)<br/>• Deduplication & String standardization<br/>• Interquartile Range (IQR) outlier filtering | `pages/2_Data_Preprocessing.py`<br/>`pages/3_Exploratory_Analysis.py`<br/>`modules/data_cleaning.py`<br/>`modules/statistical_analysis.py`<br/>IQR bounds: $[Q_1 - 1.5\text{IQR}, Q_3 + 1.5\text{IQR}]$ |
| **Module 3: Advanced Pandas & Visualization** | • Hierarchical indexing (MultiIndex)<br/>• Unstacking (`.unstack()`) & Stacking (`.stack()`)<br/>• Relational merging (`pd.merge()`)<br/>• Wide/long reshaping (`pd.melt()`, `df.pivot()`)<br/>• Matplotlib & Seaborn statistical plots<br/>• Plotly interactive web canvases | `pages/4_Visualizations.py`<br/>`pages/5_Data_Aggregation.py`<br/>`modules/visualization.py`<br/>`modules/aggregation.py`<br/>Histograms + KDE, boxplots, heatmaps |
| **Module 4: Aggregation, GroupBy & Time Series** | • GroupBy split-apply-combine<br/>• Pivot tables with margins (`margins=True`)<br/>• Cross-tabulation (`pd.crosstab()`)<br/>• DatetimeIndex & date parsing<br/>• Frequency resampling (`ME`, `QE`, `YE`)<br/>• Moving averages & rolling volatility (3-mo, 6-mo)<br/>• Shifting & lag growth rates (`shift(1)`, MoM)<br/>• Period arithmetic & Timezone localization | `pages/5_Data_Aggregation.py`<br/>`pages/6_Time_Series_Analysis.py`<br/>`pages/7_Future_Technology_Insights.py`<br/>`pages/8_Reports.py`<br/>`modules/time_series.py`<br/>`modules/opportunity_analysis.py` |

---

## 9. Verification & Automated Test Suites

Run the complete 30-test suite locally:

```powershell
python tests\test_analytics.py
python tests\test_multi_period.py
python tests\test_collectors.py
```

* **`tests/test_analytics.py` (11 Tests):** Validates all CSA4503 curriculum topics (imputation, IQR outlier filtering, descriptive statistics, correlation matrices, GroupBy, pivot tables, time series resampling, opportunity scoring, and PDF generation).
* **`tests/test_multi_period.py` (8 Tests):** Validates zero-safe growth calculations, 7-day and 30-day moving averages, growth acceleration, live intelligence ranking, and SQLite persistence.
* **`tests/test_collectors.py` (11 Tests):** Validates GitHub, Hugging Face, Adzuna, and Google Trends collectors with mocked HTTP responses, rate-limiting handlers, Adzuna CSV skill extraction, database deduplication, and status logging.

---

## 10. License & Academic Attribution

Developed as an MCA Mini-Project for **CSA4503 Data Analytics and Visualization**. Free for educational demonstration, academic viva, and research use.
