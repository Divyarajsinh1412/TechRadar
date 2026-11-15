"""
TechRadar — Hugging Face Hub API Collector
Queries official Hugging Face Hub REST API endpoints for AI/ML framework ecosystem intelligence:
downloads, community likes, model counts, and library adoption.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collectors.base_collector import BaseCollector
from modules.data_generator import TECH_CATEGORIES

logger = logging.getLogger("TechRadar.HuggingFaceCollector")

# Mapping of AI/ML technologies to Hugging Face query keywords/tags
HF_FRAMEWORK_MAP = {
    "PyTorch": {"search": "pytorch", "tag": "pytorch"},
    "TensorFlow": {"search": "tensorflow", "tag": "tf"},
    "Hugging Face": {"search": "transformers", "tag": "transformers"},
    "LangChain": {"search": "langchain", "tag": "langchain"},
    "Scikit-Learn": {"search": "sklearn", "tag": "sklearn"},
    "OpenCV": {"search": "opencv", "tag": "vision"},
    "Python": {"search": "python", "tag": "python"},
    "FastAPI": {"search": "fastapi", "tag": "inference"}
}

class HuggingFaceCollector(BaseCollector):
    """
    Collector for Hugging Face Hub ecosystem metrics.
    """
    API_MODELS_URL = "https://huggingface.co/api/models"

    def __init__(self):
        super().__init__(source_id="huggingface", source_name="Hugging Face Hub API")

    def collect(self, technologies: Optional[List[str]] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Query Hugging Face API for model counts, downloads, and community likes.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        observations = []

        if not technologies:
            technologies = list(HF_FRAMEWORK_MAP.keys())

        for tech in technologies:
            query_info = HF_FRAMEWORK_MAP.get(tech, {"search": tech.lower(), "tag": tech.lower()})
            params = {
                "search": query_info["search"],
                "sort": "downloads",
                "direction": "-1",
                "limit": top_k,
                "full": "false"
            }

            try:
                resp = self.session.get(self.API_MODELS_URL, params=params, timeout=self.timeout)

                if resp.status_code == 429:
                    logger.warning("Hugging Face API rate-limited (429). Pausing collector.")
                    break

                if resp.status_code != 200:
                    logger.warning(f"Hugging Face query failed for {tech}: {resp.status_code}")
                    continue

                models = resp.json()
                if not isinstance(models, list) or not models:
                    continue

                total_downloads = sum(m.get("downloads", 0) for m in models)
                total_likes = sum(m.get("likes", 0) for m in models)
                model_count = len(models)
                source_url = f"https://huggingface.co/models?search={query_info['search']}"

                cat = "AI & Machine Learning"

                observations.extend([
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "huggingface",
                        "metric_name": "hf_downloads",
                        "metric_value": total_downloads,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    },
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "huggingface",
                        "metric_name": "hf_likes",
                        "metric_value": total_likes,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    },
                    {
                        "observation_date": today_str,
                        "technology": tech,
                        "category": cat,
                        "source_id": "huggingface",
                        "metric_name": "hf_models_tracked",
                        "metric_value": model_count,
                        "data_frequency": "daily",
                        "data_quality_status": "verified_live",
                        "source_url": source_url
                    }
                ])

                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error querying Hugging Face API for '{tech}': {e}")
                continue

        return observations
