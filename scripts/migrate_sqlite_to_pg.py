"""
TechRadar — SQLite to Supabase PostgreSQL Migration Script
Migrates all historical technology metrics, live multi-period observations,
data source statuses, and uploaded datasets from local SQLite into Supabase PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_pg.py
    python scripts/migrate_sqlite_to_pg.py --postgres-url "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
"""

import os
import sys
import argparse
import sqlite3
import logging
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("TechRadar.Migration")

DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "techradar.db")
POSTGRES_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "postgres_schema.sql")

TABLES_TO_MIGRATE = [
    "technologies",
    "categories",
    "technology_metrics",
    "live_observations",
    "data_source_status",
    "uploaded_datasets",
    "raw_job_postings",
    "collection_history"
]

def parse_args():
    parser = argparse.ArgumentParser(description="Migrate TechRadar data from SQLite to Supabase PostgreSQL")
    parser.add_argument("--sqlite-path", default=DEFAULT_SQLITE_PATH, help="Path to source SQLite database")
    parser.add_argument("--postgres-url", default=os.environ.get("DATABASE_URL"), help="Target Supabase PostgreSQL URL")
    return parser.parse_args()

def init_postgres_schema(pg_engine: sa.Engine):
    """Execute DDL schema on PostgreSQL target."""
    logger.info("Initializing Supabase PostgreSQL schema...")
    with open(POSTGRES_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
    with pg_engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info("Supabase PostgreSQL schema initialized successfully.")

def migrate_table(table_name: str, sqlite_conn: sqlite3.Connection, pg_engine: sa.Engine) -> int:
    """Migrate a single table from SQLite to PostgreSQL with type conversion and conflict handling."""
    # Check if table exists in SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        logger.info(f"Skipping '{table_name}' (not present in SQLite source).")
        return 0

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    if df.empty:
        logger.info(f"Table '{table_name}' is empty. 0 rows migrated.")
        return 0

    # Clean DataFrame column names
    df.columns = [c.lower() for c in df.columns]

    # Drop local SQLite auto-increment primary key 'id' to let Postgres SERIAL generate primary keys
    if "id" in df.columns and table_name != "technologies" and table_name != "categories":
        df = df.drop(columns=["id"])

    logger.info(f"Migrating {len(df)} records for '{table_name}'...")

    with pg_engine.begin() as conn:
        if table_name == "data_source_status":
            # Upsert on source_id
            for _, row in df.iterrows():
                conn.execute(
                    text("""
                        INSERT INTO data_source_status (source_id, source_name, last_refresh, status, available_frequency, records_count, message)
                        VALUES (:source_id, :source_name, :last_refresh, :status, :available_frequency, :records_count, :message)
                        ON CONFLICT (source_id) DO UPDATE SET
                            last_refresh = EXCLUDED.last_refresh,
                            status = EXCLUDED.status,
                            records_count = EXCLUDED.records_count,
                            message = EXCLUDED.message
                    """),
                    row.to_dict()
                )
        elif table_name == "live_observations":
            # Upsert on composite unique key
            for _, row in df.iterrows():
                conn.execute(
                    text("""
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
                            collection_timestamp = EXCLUDED.collection_timestamp
                    """),
                    {
                        "observation_date": str(row["observation_date"]),
                        "technology": str(row["technology"]),
                        "category": str(row.get("category", "General")),
                        "source_id": str(row["source_id"]),
                        "metric_name": str(row["metric_name"]),
                        "metric_value": float(row["metric_value"]),
                        "data_frequency": str(row.get("data_frequency", "daily")),
                        "data_quality_status": str(row.get("data_quality_status", "verified_live")),
                        "source_url": row.get("source_url"),
                        "collection_timestamp": str(row.get("collection_timestamp", datetime.now().isoformat()))
                    }
                )
        elif table_name == "technology_metrics":
            # Bulk insert metrics ignoring duplicates
            for _, row in df.iterrows():
                conn.execute(
                    text("""
                        INSERT INTO technology_metrics (
                            technology, category, year, month, date,
                            job_postings, developer_interest, company_adoption,
                            average_salary, github_activity, skill_demand, growth_rate
                        ) VALUES (
                            :technology, :category, :year, :month, :date,
                            :job_postings, :developer_interest, :company_adoption,
                            :average_salary, :github_activity, :skill_demand, :growth_rate
                        )
                        ON CONFLICT (technology, date) DO NOTHING
                    """),
                    row.to_dict()
                )
        else:
            df.to_sql(table_name, conn, if_exists="append", index=False)

    logger.info(f"Successfully migrated '{table_name}': {len(df)} rows.")
    return len(df)

def main():
    args = parse_args()
    pg_url = args.postgres_url

    if not pg_url:
        logger.error("DATABASE_URL is not provided. Set DATABASE_URL in environment or pass --postgres-url.")
        sys.exit(1)

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    if not os.path.exists(args.sqlite_path):
        logger.error(f"Source SQLite database not found at: {args.sqlite_path}")
        sys.exit(1)

    logger.info(f"Connecting to SQLite: {args.sqlite_path}")
    sqlite_conn = sqlite3.connect(args.sqlite_path)

    logger.info("Connecting to target PostgreSQL database...")
    pg_engine = create_engine(
        pg_url,
        poolclass=sa.pool.NullPool,
        connect_args={"sslmode": "require"} if "sslmode" not in pg_url else {}
    )

    try:
        # 1. Initialize schema
        init_postgres_schema(pg_engine)

        # 2. Migrate tables
        total_migrated = 0
        for table in TABLES_TO_MIGRATE:
            total_migrated += migrate_table(table, sqlite_conn, pg_engine)

        logger.info(f"MIGRATION COMPLETE: Migrated a total of {total_migrated} records into Supabase PostgreSQL!")
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    main()
