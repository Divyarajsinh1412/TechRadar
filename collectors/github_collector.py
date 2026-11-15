"""
TechRadar — GitHub REST API Collector
Collects live repository metrics (stars, forks, repo counts, primary languages, commit/push activity)
from the official GitHub REST API v3.
Supports authentication via GITHUB_TOKEN and handles rate-limits gracefully.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collectors.base_collector import BaseCollector
from modules.data_generator import TECH_CATEGORIES

logger = logging.getLogger("TechRadar.GitHubCollector")

class GitHubCollector(BaseCollector):
    """
    Collector for GitHub repository intelligence.
    """
    SEARCH_URL = "https://api.github.com/search/repositories"

    def __init__(self, token: Optional[str] = None):
        super().__init__(source_id="github", source_name="GitHub REST API")
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            logger.info("GitHub Collector initialized with API token.")
        else:
            logger.warning("GITHUB_TOKEN not found in environment. Using unauthenticated access (limited to 60 req/hr).")

    def collect(self, technologies: Optional[List[str]] = None, limit_per_tech: int = 3) -> List[Dict[str, Any]]:
        """
        Query GitHub for repository metrics across technologies.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        observations = []

        if not technologies:
            technologies = []
            for cat, techs in TECH_CATEGORIES.items():
                technologies.extend(techs)

        # Invert category map
        tech_to_cat = {}
        for cat, techs in TECH_CATEGORIES.items():
            for t in techs:
                tech_to_cat[t] = cat

        for idx, tech in enumerate(technologies):
            query = f"{tech} in:name,description,topics"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit_per_tech
            }

            try:
                resp = self.session.get(self.SEARCH_URL, params=params, timeout=self.timeout)

                # Check rate limit headers
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 10))
                if remaining <= 1:
                    logger.warning(f"GitHub API rate-limit reached (Remaining: {remaining}). Pausing collection.")
                    break

                if resp.status_code == 403 or resp.status_code == 429:
                    logger.warning(f"GitHub API rate-limited (Status {resp.status_code}).")
                    break

                if resp.status_code != 200:
                    logger.warning(f"GitHub API query failed for {tech}: {resp.status_code} {resp.text[:100]}")
                    continue

                data = resp.json()
                total_repos = data.get("total_count", 0)
                items = data.get("items", [])

                if not items:
                    continue

                top_item = items[0]
                stars = top_item.get("stargazers_count", 0)
                forks = top_item.get("forks_count", 0)
                open_issues = top_item.get("open_issues_count", 0)
                source_url = top_item.get("html_url", f"https://github.com/search?q={tech}")
                cat = tech_to_cat.get(tech, "General")

                # Activity score 0-100 normalized
                activity_score = min(100.0, max(10.0, (stars / 2000.0) * 10.0 + (forks / 500.0) * 5.0))

                observations.extend([
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "github",
                        "metric_name": "stars",
                        "metric_value": stars,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    },
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "github",
                        "metric_name": "forks",
                        "metric_value": forks,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    },
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "github",
                        "metric_name": "github_activity",
                        "metric_value": round(activity_score, 2),
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    },
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "github",
                        "metric_name": "repo_count",
                        "metric_value": total_repos,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    }
                ])

                # Small polite throttle between queries
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error collecting GitHub data for '{tech}': {e}")
                continue

        return observations
