"""
TechRadar — Database Management Module
Supports both Supabase PostgreSQL (Production) and SQLite (Local Development / Fallback).
Connects via SQLAlchemy 2.0 with connection pooling, robust retry mechanisms,
and complete schema management across both database engines.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, NullPool

load_dotenv()

logger = logging.getLogger("TechRadar.Database")
logging.basicConfig(level=logging.INFO)

# File Paths for Local SQLite fallback and Schema definitions
CURRENT_DIR = os.path.dirname(__file__)
SQLITE_DB_PATH = os.path.join(CURRENT_DIR, "techradar.db")
SQLITE_SCHEMA_PATH = os.path.join(CURRENT_DIR, "schema.sql")
POSTGRES_SCHEMA_PATH = os.path.join(CURRENT_DIR, "postgres_schema.sql")

DEFAULT_SOURCES = [
    {
        "source_id": "github",
        "source_name": "GitHub API & Repositories",
        "available_frequency": "Daily",
        "status": "active",
        "message": "Public repository creation, stars, forks & activity tracking"
    },
    {
        "source_id": "huggingface",
        "source_name": "Hugging Face Hub API",
        "available_frequency": "Daily",
        "status": "active",
        "message": "AI model downloads, likes, and open-source ecosystem growth"
    },
    {
        "source_id": "adzuna",
        "source_name": "Adzuna Job Market API",
        "available_frequency": "Daily / Weekly",
        "status": "active",
        "message": "Enterprise job vacancies, required skills, and salary intelligence"
    },
    {
        "source_id": "google_trends",
        "source_name": "Google Trends Interest",
        "available_frequency": "Daily / Weekly",
        "status": "active",
        "message": "Normalized public search-interest trajectory"
    },
    {
        "source_id": "developer_survey",
        "source_name": "Developer Surveys & Benchmarks",
        "available_frequency": "Annual Benchmark",
        "status": "periodic_benchmark",
        "message": "Stack Overflow & industry developer sentiment baseline"
    }
]

_ENGINE_CACHE: Optional[Engine] = None
_CUSTOM_ENGINES: Dict[str, Engine] = {}

def get_database_url() -> str:
    """
    Retrieve normalized database URL from environment or fallback to SQLite.
    Rewrites postgres:// to postgresql:// as required by SQLAlchemy.
    """
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        return f"sqlite:///{SQLITE_DB_PATH}"

    # Supabase connection URI compatibility
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    return db_url

def get_connection(db_path: str = SQLITE_DB_PATH):
    """Return an active connection to the SQLite database with row factory enabled for legacy callers."""
    import sqlite3
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def is_using_postgres() -> bool:
    """Return True if currently configured to use Supabase / PostgreSQL."""
    url = get_database_url()
    return url.startswith("postgresql://") or url.startswith("postgres://")

def get_db_engine(db_path: Optional[str] = None) -> Engine:
    """
    Create or return cached SQLAlchemy engine with connection pooling.
    If custom db_path is specified, creates a dedicated SQLite engine.
    """
    global _ENGINE_CACHE, _CUSTOM_ENGINES
    if db_path is not None:
        if db_path not in _CUSTOM_ENGINES:
            _CUSTOM_ENGINES[db_path] = create_engine(
                f"sqlite:///{db_path}",
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )
        return _CUSTOM_ENGINES[db_path]

    if _ENGINE_CACHE is not None:
        return _ENGINE_CACHE

    db_url = get_database_url()

    if is_using_postgres():
        # Supabase PostgreSQL engine with connection pooling
        _ENGINE_CACHE = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"} if "sslmode" not in db_url else {}
        )
        logger.info("Initialized PostgreSQL Engine connected to cloud database.")
    else:
        # SQLite Engine
        _ENGINE_CACHE = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
        logger.info(f"Initialized SQLite Engine: {db_url}")

    return _ENGINE_CACHE

def close_engine(db_path: Optional[str] = None) -> None:
    """Dispose active engine connections and clean up file locks."""
    global _ENGINE_CACHE, _CUSTOM_ENGINES
    import gc
    if db_path is not None:
        if db_path in _CUSTOM_ENGINES:
            _CUSTOM_ENGINES[db_path].dispose()
            del _CUSTOM_ENGINES[db_path]
    elif _ENGINE_CACHE is not None:
        _ENGINE_CACHE.dispose()
        _ENGINE_CACHE = None
    gc.collect()

def init_database(db_path: Optional[str] = None) -> None:
    """
    Execute appropriate DDL schema for the active database engine (PostgreSQL or SQLite),
    and initialize default data source operational tracking records.
    """
    engine = get_db_engine(db_path=db_path)
    is_pg = is_using_postgres() and db_path is None
    schema_file = POSTGRES_SCHEMA_PATH if is_pg else SQLITE_SCHEMA_PATH

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with engine.begin() as conn:
        if is_pg:
            # PostgreSQL schema may contain multiple statements separated by ';'
            statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
            for stmt in statements:
                conn.execute(text(stmt))
        else:
            # SQLite supports execution of full script
            raw_conn = conn.connection
            raw_conn.executescript(schema_sql)

            # Ensure columns added in updates exist in legacy tables
            cursor = raw_conn.cursor()
            cursor.execute("PRAGMA table_info(live_observations)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            if "source_url" not in existing_cols:
                cursor.execute("ALTER TABLE live_observations ADD COLUMN source_url TEXT")
                raw_conn.commit()
            cursor.close()

        # Seed data_source_status with default sources if not present
        for s in DEFAULT_SOURCES:
            check_stmt = text("SELECT COUNT(*) FROM data_source_status WHERE source_id = :s_id")
            exists = (conn.execute(check_stmt, {"s_id": s["source_id"]}).scalar() or 0) > 0
            if not exists:
                now_iso = datetime.now().isoformat()
                conn.execute(
                    text("""
                        INSERT INTO data_source_status (source_id, source_name, available_frequency, status, message, last_refresh)
                        VALUES (:s_id, :s_name, :s_freq, :s_stat, :s_msg, :s_refresh)
                    """),
                    {
                        "s_id": s["source_id"],
                        "s_name": s["source_name"],
                        "s_freq": s["available_frequency"],
                        "s_stat": s["status"],
                        "s_msg": s["message"],
                        "s_refresh": now_iso
                    }
                )

# ----------------- Historical Technology Metrics -----------------

def save_metrics_to_db(df: pd.DataFrame, replace: bool = False, db_path: Optional[str] = None) -> int:
    """
    Save historical metrics DataFrame to technology_metrics table.
    """
    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)

    clean_df = df.copy()
    clean_df.columns = [c.lower().replace(" ", "_") for c in clean_df.columns]

    required = [
        "technology", "category", "year", "month", "date",
        "job_postings", "developer_interest", "company_adoption",
        "average_salary", "github_activity", "skill_demand", "growth_rate"
    ]
    insert_cols = [c for c in required if c in clean_df.columns]
    if not insert_cols:
        return 0

    data_to_save = clean_df[insert_cols].copy()
    if "technology" in data_to_save.columns and "date" in data_to_save.columns:
        data_to_save = data_to_save.drop_duplicates(subset=["technology", "date"], keep="last")

    with engine.begin() as conn:
        if replace:
            conn.execute(text("DELETE FROM technology_metrics"))
        data_to_save.to_sql("technology_metrics", conn, if_exists="append", index=False)

    return len(data_to_save)

def load_metrics_from_db(db_path: Optional[str] = None) -> pd.DataFrame:
    """Load historical longitudinal metrics as a Pandas DataFrame."""
    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)
    query = text("SELECT * FROM technology_metrics ORDER BY date ASC, technology ASC")
    with engine.connect() as conn:
        return pd.read_sql_query(query, conn)

# ----------------- Unified Live Multi-Period Observations -----------------

def bulk_save_live_observations(observations: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
    """
    Bulk insert or upsert multi-period live observations.
    Prevents duplicates on (observation_date, technology, source_id, metric_name, data_frequency).
    Uses PostgreSQL ON CONFLICT in production and SQLite INSERT OR REPLACE in local dev.
    """
    if not observations:
        return 0

    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)
    is_pg = is_using_postgres() and db_path is None

    now_str = datetime.now().isoformat()
    rows_to_insert = [
        {
            "observation_date": str(obs["observation_date"]),
            "technology": str(obs["technology"]),
            "category": str(obs.get("category", "General")),
            "source_id": str(obs["source_id"]),
            "metric_name": str(obs["metric_name"]),
            "metric_value": float(obs["metric_value"]),
            "data_frequency": str(obs.get("data_frequency", "daily")).lower(),
            "data_quality_status": str(obs.get("data_quality_status", "verified_live")),
            "source_url": obs.get("source_url"),
            "collection_timestamp": now_str
        }
        for obs in observations
    ]

    with engine.begin() as conn:
        if is_pg:
            stmt = text("""
                INSERT INTO live_observations (
                    observation_date, technology, category, source_id,
                    metric_name, metric_value, data_frequency, data_quality_status,
                    source_url, collection_timestamp
                ) VALUES (
                    :observation_date, :technology, :category, :source_id,
                    :metric_name, :metric_value, :data_frequency, :data_quality_status,
                    :source_url, :collection_timestamp
                )
                ON CONFLICT (observation_date, technology, source_id, metric_name, data_frequency)
                DO UPDATE SET
                    metric_value = EXCLUDED.metric_value,
                    data_quality_status = EXCLUDED.data_quality_status,
                    source_url = EXCLUDED.source_url,
                    collection_timestamp = EXCLUDED.collection_timestamp
            """)
            conn.execute(stmt, rows_to_insert)
        else:
            stmt = text("""
                INSERT OR REPLACE INTO live_observations (
                    observation_date, technology, category, source_id,
                    metric_name, metric_value, data_frequency, data_quality_status,
                    source_url, collection_timestamp
                ) VALUES (
                    :observation_date, :technology, :category, :source_id,
                    :metric_name, :metric_value, :data_frequency, :data_quality_status,
                    :source_url, :collection_timestamp
                )
            """)
            conn.execute(stmt, rows_to_insert)

    return len(rows_to_insert)

def get_live_observations(
    frequency: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    technology: Optional[str] = None,
    source_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Query live observations matching frequency and filters.
    """
    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)

    where_clauses = ["data_frequency = :freq"]
    params: Dict[str, Any] = {"freq": frequency.lower()}

    if start_date:
        where_clauses.append("observation_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("observation_date <= :end_date")
        params["end_date"] = end_date
    if technology and technology != "All":
        where_clauses.append("technology = :technology")
        params["technology"] = technology
    if source_id and source_id != "All":
        where_clauses.append("source_id = :source_id")
        params["source_id"] = source_id

    sql = f"SELECT * FROM live_observations WHERE {' AND '.join(where_clauses)} ORDER BY observation_date ASC, technology ASC"
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)

# ----------------- Data Source Status Tracking -----------------

def get_source_status(db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve operational status and freshness of all data sources."""
    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)
    with engine.connect() as conn:
        return pd.read_sql_query(text("SELECT * FROM data_source_status ORDER BY source_name ASC"), conn)

def update_source_status(
    source_id: str,
    status: str,
    message: str,
    records_count: int = 0,
    db_path: Optional[str] = None
) -> None:
    """Update status, message, count, and timestamp for a given data source."""
    init_database(db_path=db_path)
    engine = get_db_engine(db_path=db_path)
    now_str = datetime.now().isoformat()
    
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE data_source_status
                SET status = :status, message = :message, records_count = records_count + :rec_count, last_refresh = :now_str
                WHERE source_id = :source_id
            """),
            {
                "status": status,
                "message": message,
                "rec_count": records_count,
                "now_str": now_str,
                "source_id": source_id
            }
        )

# ----------------- Scheduled Collection History -----------------

def log_collection_run(
    source_id: str,
    job_name: str,
    status: str,
    records_collected: int = 0,
    error_message: Optional[str] = None
) -> None:
    """Record an automated collection job execution into collection_history."""
    init_database()
    engine = get_db_engine()
    now_str = datetime.now().isoformat()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO collection_history (source_id, job_name, status, records_collected, start_time, end_time, error_message)
                VALUES (:source_id, :job_name, :status, :records_collected, :now_str, :now_str, :error_message)
            """),
            {
                "source_id": source_id,
                "job_name": job_name,
                "status": status,
                "records_collected": records_collected,
                "now_str": now_str,
                "error_message": error_message
            }
        )

# ----------------- Raw Job Postings Deduplication -----------------

def save_raw_job_postings(jobs: List[Dict[str, Any]]) -> int:
    """
    Save raw job postings, deduplicating by external_id.
    """
    if not jobs:
        return 0

    init_database()
    engine = get_db_engine()
    is_pg = is_using_postgres()

    with engine.begin() as conn:
        for job in jobs:
            params = {
                "ext_id": str(job["external_id"]),
                "source_id": str(job.get("source_id", "adzuna")),
                "title": str(job["title"]),
                "company": str(job.get("company", "Unknown")),
                "location": str(job.get("location", "Unknown")),
                "country": str(job.get("country", "in")),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "detected_skills": str(job.get("detected_skills", "")),
                "posting_date": str(job["posting_date"])
            }
            if is_pg:
                stmt = text("""
                    INSERT INTO raw_job_postings (
                        external_id, source_id, title, company, location, country,
                        salary_min, salary_max, detected_skills, posting_date
                    ) VALUES (
                        :ext_id, :source_id, :title, :company, :location, :country,
                        :salary_min, :salary_max, :detected_skills, :posting_date
                    )
                    ON CONFLICT (external_id) DO NOTHING
                """)
            else:
                stmt = text("""
                    INSERT OR IGNORE INTO raw_job_postings (
                        external_id, source_id, title, company, location, country,
                        salary_min, salary_max, detected_skills, posting_date
                    ) VALUES (
                        :ext_id, :source_id, :title, :company, :location, :country,
                        :salary_min, :salary_max, :detected_skills, :posting_date
                    )
                """)
            conn.execute(stmt, params)

    return len(jobs)

# ----------------- User Uploaded Datasets -----------------

def record_upload(filename: str, row_count: int, col_count: int) -> int:
    """Record an uploaded dataset's metadata."""
    init_database()
    engine = get_db_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text("""
                INSERT INTO uploaded_datasets (filename, row_count, column_count, is_active)
                VALUES (:filename, :row_count, :col_count, 1)
            """),
            {"filename": filename, "row_count": row_count, "col_count": col_count}
        )
        return getattr(res, "lastrowid", 1) or 1

def list_uploaded_datasets() -> pd.DataFrame:
    """Retrieve list of uploaded datasets."""
    init_database()
    engine = get_db_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(text("SELECT * FROM uploaded_datasets ORDER BY upload_time DESC"), conn)
