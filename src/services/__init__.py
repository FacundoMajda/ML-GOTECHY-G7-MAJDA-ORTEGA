# src/services/__init__.py
from src.services.analytics_service import AnalyticsService
from src.services.report_service import generate_report_html

__all__ = [
    "AnalyticsService",
    "generate_report_html",
]
