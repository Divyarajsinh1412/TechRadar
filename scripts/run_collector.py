"""
TechRadar — Automated Real Data Collection CLI & Render Cron Runner
Executes individual or unified data collection jobs across GitHub, Hugging Face,
Adzuna, Google Trends, and Developer Surveys.

Designed for Render Cron Jobs:
- GitHub: every 6 hours
- Hugging Face: every 6 hours
- Job market: every 12 hours
- Google Trends: daily

Usage:
    python scripts/run_collector.py --source github
    python scripts/run_collector.py --source huggingface
    python scripts/run_collector.py --source adzuna
    python scripts/run_collector.py --source google_trends
    python scripts/run_collector.py --source all
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from collectors import (
    GitHubCollector,
    HuggingFaceCollector,
    AdzunaCollector,
    GoogleTrendsCollector,
    DeveloperSurveyCollector
)
from database.db import init_database, get_source_status, is_using_postgres

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("TechRadar.Cron")

COLLECTOR_MAP = {
    "github": GitHubCollector,
    "huggingface": HuggingFaceCollector,
    "adzuna": AdzunaCollector,
    "google_trends": GoogleTrendsCollector,
    "survey": DeveloperSurveyCollector
}

def parse_args():
    parser = argparse.ArgumentParser(description="TechRadar Real Data Collection Runner")
    parser.add_argument(
        "--source",
        choices=["github", "huggingface", "adzuna", "google_trends", "survey", "all"],
        default="all",
        help="Target data source collector to run"
    )
    parser.add_argument(
        "--tech",
        nargs="+",
        default=None,
        help="Optional subset of technologies to collect (e.g. Python Rust PyTorch)"
    )
    return parser.parse_args()

def run_single_collector(source_key: str, technologies=None) -> bool:
    """Run a single collector and return True on success or partial success."""
    collector_cls = COLLECTOR_MAP.get(source_key)
    if not collector_cls:
        logger.error(f"Unknown collector source: {source_key}")
        return False

    try:
        collector = collector_cls()
        result = collector.run(technologies=technologies)
        logger.info(f"Collector '{source_key}' finished with status: {result['status']}, records: {result['count']}")
        return result["status"] in ["success", "partial"]
    except Exception as e:
        logger.error(f"Fatal unhandled exception in collector '{source_key}': {e}", exc_info=True)
        return False

def main():
    args = parse_args()
    logger.info("Initializing database connection...")
    init_database()
    logger.info(f"Database Target: {'Supabase PostgreSQL (Production)' if is_using_postgres() else 'SQLite (Local / Fallback)'}")

    start_time = datetime.now()
    sources_to_run = list(COLLECTOR_MAP.keys()) if args.source == "all" else [args.source]
    
    logger.info(f"Starting collection run for: {sources_to_run}")

    all_successful = True
    for src in sources_to_run:
        success = run_single_collector(src, technologies=args.tech)
        if not success:
            all_successful = False

    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Collection run completed in {duration:.2f}s. All successful?: {all_successful}")

    # Exit cleanly for cron runners
    sys.exit(0 if all_successful else 1)

if __name__ == "__main__":
    main()
