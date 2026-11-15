"""
TechRadar — Adzuna Job Market API & Real CSV Import Collector
Collects job titles, companies, locations, salaries, and extracts technology skills
from the official Adzuna REST API (with support for India 'in', US, and UK).
Deduplicates postings in the database and supports CSV file imports when API keys are absent.
"""

import os
import re
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from collectors.base_collector import BaseCollector
from database.db import save_raw_job_postings
from modules.data_generator import TECH_CATEGORIES

logger = logging.getLogger("TechRadar.AdzunaCollector")

class AdzunaCollector(BaseCollector):
    """
    Collector for hiring market data via Adzuna API and CSV import fallback.
    """
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: Optional[str] = None
    ):
        super().__init__(source_id="adzuna", source_name="Adzuna Job Market API")
        self.app_id = app_id or os.environ.get("ADZUNA_APP_ID")
        self.app_key = app_key or os.environ.get("ADZUNA_APP_KEY")
        self.country = country or os.environ.get("ADZUNA_COUNTRY", "in").lower()

        if self.app_id and self.app_key:
            logger.info(f"Adzuna Collector initialized with App ID for country: {self.country.upper()}")
        else:
            logger.warning("ADZUNA_APP_ID / ADZUNA_APP_KEY not configured. CSV import mode enabled.")

    def is_configured(self) -> bool:
        """Return True if real API credentials are present."""
        return bool(self.app_id and self.app_key)

    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Identify canonical technologies mentioned in job title and description.
        """
        detected = []
        text_lower = text.lower()
        for cat, techs in TECH_CATEGORIES.items():
            for tech in techs:
                # Word-boundary matching to prevent false positives (e.g. 'go' in 'good')
                pattern = r'\b' + re.escape(tech.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    detected.append(tech)
        return list(set(detected))

    def collect(self, technologies: Optional[List[str]] = None, max_pages: int = 2) -> List[Dict[str, Any]]:
        """
        Query Adzuna API for technology skills demand and salaries.
        """
        if not self.is_configured():
            logger.warning("Adzuna API credentials not configured. Skipping live API fetch.")
            return []

        today_str = datetime.now().strftime("%Y-%m-%d")
        observations = []
        raw_jobs = []

        if not technologies:
            technologies = []
            for cat, techs in TECH_CATEGORIES.items():
                technologies.extend(techs)

        # Invert category map
        tech_to_cat = {}
        for cat, techs in TECH_CATEGORIES.items():
            for t in techs:
                tech_to_cat[t] = cat

        for tech in technologies:
            url = f"{self.BASE_URL}/{self.country}/search/1"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "what": tech,
                "category": "it-jobs",
                "results_per_page": 20,
                "content-type": "application/json"
            }

            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)

                if resp.status_code == 403 or resp.status_code == 401:
                    logger.error(f"Adzuna API authentication error ({resp.status_code}): Invalid APP_ID or APP_KEY.")
                    break

                if resp.status_code == 429:
                    logger.warning("Adzuna API rate-limit reached (429). Pausing collector.")
                    break

                if resp.status_code != 200:
                    logger.warning(f"Adzuna query failed for {tech}: {resp.status_code}")
                    continue

                data = resp.json()
                total_count = data.get("count", 0)
                results = data.get("results", [])

                salaries = []
                for item in results:
                    job_id = str(item.get("id"))
                    title = item.get("title", "")
                    company = item.get("company", {}).get("display_name", "Unknown")
                    loc = item.get("location", {}).get("display_name", "Unknown")
                    s_min = item.get("salary_min")
                    s_max = item.get("salary_max")
                    desc = item.get("description", "")
                    source_url = item.get("redirect_url", "")

                    if s_min and s_max:
                        salaries.append((s_min + s_max) / 2.0)
                    elif s_min:
                        salaries.append(s_min)

                    detected = self.extract_skills_from_text(f"{title} {desc}")
                    if tech not in detected:
                        detected.append(tech)

                    raw_jobs.append({
                        "external_id": job_id,
                        "source_id": "adzuna",
                        "title": title,
                        "company": company,
                        "location": loc,
                        "country": self.country,
                        "salary_min": s_min,
                        "salary_max": s_max,
                        "detected_skills": ", ".join(detected),
                        "posting_date": today_str
                    })

                avg_salary = (sum(salaries) / len(salaries)) if salaries else 0.0
                cat = tech_to_cat.get(tech, "General")
                source_url = f"https://www.adzuna.in/search?q={tech}" if self.country == "in" else f"https://www.adzuna.com/search?q={tech}"

                observations.append({
                    "observation_date": today_str,
                    "technology": tech,
                    "category": cat,
                    "source_id": "adzuna",
                    "metric_name": "job_postings",
                    "metric_value": total_count,
                    "data_frequency": "daily",
                    "data_quality_status": "verified_live",
                    "source_url": source_url
                })

                if avg_salary > 0:
                    observations.append({
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "adzuna",
                        "metric_name": "average_salary",
                        "metric_value": round(avg_salary, 2),
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    })

                time.sleep(0.3)

            except Exception as e:
                logger.error(f"Error querying Adzuna API for '{tech}': {e}")
                continue

        # Save and deduplicate raw postings
        if raw_jobs:
            save_raw_job_postings(raw_jobs)

        return observations

    def import_jobs_from_csv(self, file_source: Any) -> List[Dict[str, Any]]:
        """
        Process user-imported real CSV job postings (e.g. from Kaggle/LinkedIn job datasets)
        and extract canonical technology skill observations without generating fake data.
        """
        if isinstance(file_source, str):
            df = pd.read_csv(file_source)
        else:
            df = pd.read_csv(file_source)

        df.columns = [c.lower().strip() for c in df.columns]
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Find title and description columns
        title_col = next((c for c in df.columns if "title" in c or "role" in c or "job" in c), None)
        desc_col = next((c for c in df.columns if "desc" in c or "summary" in c or "requirement" in c), None)

        if not title_col:
            raise ValueError("CSV must contain a 'job_title' or 'title' column.")

        # Invert category map
        tech_to_cat = {}
        for cat, techs in TECH_CATEGORIES.items():
            for t in techs:
                tech_to_cat[t] = cat

        tech_counts: Dict[str, int] = {}
        raw_jobs = []

        for idx, row in df.iterrows():
            title = str(row[title_col])
            desc = str(row[desc_col]) if desc_col else ""
            full_text = f"{title} {desc}"

            detected = self.extract_skills_from_text(full_text)
            for tech in detected:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1

            raw_jobs.append({
                "external_id": f"csv_{today_str}_{idx}",
                "source_id": "csv_import",
                "title": title[:200],
                "company": str(row.get("company", "Unknown")),
                "location": str(row.get("location", "Unknown")),
                "country": str(row.get("country", self.country)),
                "salary_min": None,
                "salary_max": None,
                "detected_skills": ", ".join(detected),
                "posting_date": today_str
            })

        if raw_jobs:
            save_raw_job_postings(raw_jobs)

        observations = []
        for tech, count in tech_counts.items():
            cat = tech_to_cat.get(tech, "General")
            observations.append({
                "observation_date": today_str,
                "technology": tech,
                "category": cat,
                "source_id": "adzuna",
                "metric_name": "job_postings",
                "metric_value": count,
                "data_frequency": "daily",
                "data_quality_status": "verified_live",
                "source_url": "csv_import"
            })

        return observations
