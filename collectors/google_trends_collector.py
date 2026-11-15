"""
TechRadar — Google Trends Interest Collector
Collects normalized search interest (0–100) using pytrends.
Handles Google Trends rate-limiting (429) gracefully without throwing uncaught exceptions.
NOTE: Values represent normalized relative search interest, NOT absolute search query volume.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collectors.base_collector import BaseCollector
from modules.data_generator import TECH_CATEGORIES

logger = logging.getLogger("TechRadar.GoogleTrendsCollector")

class GoogleTrendsCollector(BaseCollector):
    """
    Collector for Google Trends relative search interest.
    """
    def __init__(self):
        super().__init__(source_id="google_trends", source_name="Google Trends Search Interest")

    def collect(self, technologies: Optional[List[str]] = None, timeframe: str = "today 1-m") -> List[Dict[str, Any]]:
        """
        Query Google Trends for relative search interest.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        observations = []

        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.warning("pytrends package not installed. Skipping Google Trends collection.")
            return []

        if not technologies:
            technologies = []
            for cat, techs in TECH_CATEGORIES.items():
                technologies.extend(techs)

        # Invert category map
        tech_to_cat = {}
        for cat, techs in TECH_CATEGORIES.items():
            for t in techs:
                tech_to_cat[t] = cat

        try:
            pytrend = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        except Exception as e:
            logger.warning(f"Failed to initialize pytrends client: {e}")
            return []

        # Batch technologies in groups of 4 (pytrends allows max 5 keywords per request)
        batch_size = 4
        for i in range(0, min(len(technologies), 16), batch_size):
            batch = technologies[i:i + batch_size]
            try:
                pytrend.build_payload(kw_list=batch, timeframe=timeframe)
                df = pytrend.interest_over_time()

                if df is not None and not df.empty:
                    for tech in batch:
                        if tech in df.columns:
                            # Take the most recent observed relative interest
                            recent_val = float(df[tech].iloc[-1])
                            cat = tech_to_cat.get(tech, "General")
                            source_url = f"https://trends.google.com/trends/explore?q={tech}"

                            observations.append({
                                "observation_date": today_str,
                                "technology": tech,
                                "category": cat,
                                "source_id": "google_trends",
                                "metric_name": "search_interest",
                                "metric_value": round(recent_val, 2),
                                "data_frequency": "daily",
                                "data_quality_status": "verified_live",
                                "source_url": source_url
                            })

                # Polite throttle to avoid Google Trends 429 IP bans
                time.sleep(2.0)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "Too Many Requests" in err_str or "ResponseError" in err_str:
                    logger.warning(f"Google Trends rate-limited (429). Stopping further queries gracefully: {e}")
                    break
                else:
                    logger.warning(f"Google Trends batch error for {batch}: {e}")
                    continue

        return observations
