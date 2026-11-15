"""
TechRadar Collectors Package
Standardized collectors for GitHub, Hugging Face, Adzuna, Google Trends, and Developer Surveys.
"""

from collectors.base_collector import BaseCollector
from collectors.github_collector import GitHubCollector
from collectors.huggingface_collector import HuggingFaceCollector
from collectors.adzuna_collector import AdzunaCollector
from collectors.google_trends_collector import GoogleTrendsCollector
from collectors.developer_survey_collector import DeveloperSurveyCollector

__all__ = [
    "BaseCollector",
    "GitHubCollector",
    "HuggingFaceCollector",
    "AdzunaCollector",
    "GoogleTrendsCollector",
    "DeveloperSurveyCollector"
]
