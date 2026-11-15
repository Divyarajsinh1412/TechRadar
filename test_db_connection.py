"""
TechRadar — Supabase PostgreSQL Connection & Data Verification Script
Verifies live connectivity to Supabase and reports table statistics.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from .env")

# Supabase URL rewrite for SQLAlchemy compatibility
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"} if "sslmode" not in database_url else {}
)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version_str = result.scalar()
        print("==================================================")
        print("✅ SUPABASE POSTGRESQL CONNECTED SUCCESSFULLY!")
        print("==================================================")
        print("Server Version:", version_str)
        print("\n--- Live Table Row Counts in Supabase ---")
        tables = [
            "technology_metrics",
            "live_observations",
            "data_source_status",
            "raw_job_postings",
            "collection_history"
        ]
        total_rows = 0
        for table in tables:
            count = connection.execute(text(f"SELECT COUNT(1) FROM {table}")).scalar()
            print(f"  • {table:<22} : {count:,} rows")
            total_rows += count
        print(f"\nTotal Records in Supabase: {total_rows:,} rows")
        print("==================================================")
except Exception as error:
    print("❌ Database connection failed:", error)
finally:
    engine.dispose()
