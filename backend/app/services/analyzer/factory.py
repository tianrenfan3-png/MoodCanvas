from __future__ import annotations

import logging

from app.config import Settings, get_settings
from app.services.analyzer.base import MoodAnalyzer
from app.services.analyzer.mock_analyzer import MockMoodAnalyzer

logger = logging.getLogger(__name__)

_analyzer: MoodAnalyzer | None = None


def create_analyzer(settings: Settings | None = None) -> MoodAnalyzer:
    settings = settings or get_settings()
    if settings.analyzer_type == "mock":
        return MockMoodAnalyzer()
    try:
        from app.services.analyzer.clip_analyzer import CLIPMoodAnalyzer

        return CLIPMoodAnalyzer(settings)
    except ImportError as exc:
        logger.warning("CLIP unavailable (%s) — falling back to mock analyzer", exc)
        return MockMoodAnalyzer()


def get_analyzer() -> MoodAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = create_analyzer()
    return _analyzer


def reset_analyzer() -> None:
    """Reset singleton — used in tests."""
    global _analyzer
    _analyzer = None


def get_analyzer_readiness() -> dict[str, object]:
    """Report analyzer state without creating the CLIP stack on first health check."""
    if _analyzer is None:
        return {"ready": False, "device": None, "model": None}
    return {
        "ready": _analyzer.is_ready(),
        "device": _analyzer.get_device() if _analyzer.is_ready() else None,
        "model": _analyzer.get_model_name() if _analyzer.is_ready() else None,
    }
