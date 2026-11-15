"""
TechRadar — Base API Collector
Provides standardized interface, resilient retry logic, logging, rate-limit management,
and unified database persistence across all external data collectors.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from database.db import (
    bulk_save_live_observations,
    update_source_status,
    log_collection_run
)

logger = logging.getLogger("TechRadar.Collector")
logging.basicConfig(level=logging.INFO)

class BaseCollector(ABC):
    """
    Abstract base class for all external data source collectors.
    """
    def __init__(self, source_id: str, source_name: str, timeout: int = 15):
        self.source_id = source_id
        self.source_name = source_name
        self.timeout = timeout
        self.session = self._create_retry_session()

    def _create_retry_session(self, retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
        """Create a requests session with automatic retries for transient HTTP errors."""
        session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "User-Agent": "TechRadar-Analytics-Engine/2.0 (Academic Research; https://github.com/TechRadar)"
        })
        return session

    @abstractmethod
    def collect(self, technologies: Optional[List[str]] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute API collection for the target technologies.
        Must return a list of observation dictionaries matching the unified schema.
        """
        pass

    def run(self, technologies: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute collection pipeline: fetch data, save observations, update source status, and log run.
        """
        start_time = datetime.now()
        logger.info(f"[{self.source_name}] Starting collection run...")

        try:
            observations = self.collect(technologies=technologies, **kwargs)
            count = len(observations)

            if count > 0:
                saved = bulk_save_live_observations(observations)
                update_source_status(
                    source_id=self.source_id,
                    status="active",
                    message=f"Live sync successful: {count} observations ingested.",
                    records_count=count
                )
                log_collection_run(
                    source_id=self.source_id,
                    job_name=f"{self.source_id}_collector",
                    status="success",
                    records_collected=count
                )
                logger.info(f"[{self.source_name}] Ingested {count} live observations.")
                return {"status": "success", "count": count, "error": None}
            else:
                update_source_status(
                    source_id=self.source_id,
                    status="offline_cached",
                    message="0 live records returned (API offline or quota reached).",
                    records_count=0
                )
                log_collection_run(
                    source_id=self.source_id,
                    job_name=f"{self.source_id}_collector",
                    status="partial",
                    records_collected=0,
                    error_message="No records collected"
                )
                return {"status": "partial", "count": 0, "error": "No records collected"}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.source_name}] Collector error: {error_msg}")
            
            # Determine if error was rate-limiting
            is_rate_limit = "429" in error_msg or "rate limit" in error_msg.lower()
            status_tag = "rate_limited" if is_rate_limit else "error"

            update_source_status(
                source_id=self.source_id,
                status=status_tag,
                message=f"Collection failed: {error_msg[:120]}",
                records_count=0
            )
            log_collection_run(
                source_id=self.source_id,
                job_name=f"{self.source_id}_collector",
                status=status_tag,
                records_collected=0,
                error_message=error_msg
            )
            return {"status": status_tag, "count": 0, "error": error_msg}
