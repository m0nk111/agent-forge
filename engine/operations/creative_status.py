"""Creative status generators for agents.

This module provides deterministic, low-overhead creative text helpers that can be used
for logging or status updates. The generators are intentionally deterministic so that
logs remain stable across runs and unit tests can assert on their outputs.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable, List

logger = logging.getLogger(__name__)

# Toggle creative debug logs via environment variable to minimize noise when disabled.
_DEBUG_ENABLED = os.getenv("CREATIVE_STATUS_DEBUG", "0") in {"1", "true", "TRUE"}

_THEMES = {
    "bug": {
        "openings": [
            "🐛 Whispering bug sleeps",
            "🐛 Patchwork winds hum",
            "🐛 Silent tests blink",
        ],
        "middles": [
            "under refactored circuits",
            "while monitors glow in sync",
            "as asserts guard brittle dreams",
        ],
        "closures": [
            "awaiting clean green",
            "promising stable sunrise",
            "until commits bloom",
        ],
    },
    "docs": {
        "openings": [
            "📚 Pages align",
            "📚 Markdown sparkles",
            "📚 Footnotes gather",
        ],
        "middles": [
            "linking context through the fog",
            "guiding tired onboarding minds",
            "mapping workflows into light",
        ],
        "closures": [
            "readers find their path",
            "style checks hum softly",
            "anchors greet new eyes",
        ],
    },
    "ops": {
        "openings": [
            "🛠️ Pipelines breathe",
            "🛰️ Agents report",
            "🛎️ Schedulers sing",
        ],
        "middles": [
            "metrics dance with tracing ink",
            "queues align in gentle waves",
            "dashboards glow in cobalt hues",
        ],
        "closures": [
            "deployments glide smooth",
            "alerts rest easy",
            "cronjobs toast success",
        ],
    },
    "default": {
        "openings": [
            "✨ Ideas bloom",
            "🌟 Branches shimmer",
            "🎨 Commits exhale",
        ],
        "middles": [
            "across the code galaxy",
            "while linters nod quietly",
            "in review-lit halls",
        ],
        "closures": [
            "merge dreams echo on",
            "team spirits take flight",
            "next tasks softly call",
        ],
    },
}


def _select_theme(labels: Iterable[str]) -> str:
    """Select a theme based on labels, falling back to default."""
    normalized = {label.lower() for label in labels}
    if normalized.intersection({"bug", "fix", "regression"}):
        return "bug"
    if normalized.intersection({"docs", "documentation", "doc"}):
        return "docs"
    if normalized.intersection({"ops", "infrastructure", "devops", "monitoring"}):
        return "ops"
    return "default"


def _index_for_sequence(values: List[str], seed: int, offset: int = 0) -> str:
    """Pick a deterministic item from *values* using the provided seed."""
    if not values:
        raise ValueError("values must not be empty")
    idx = (seed + offset) % len(values)
    return values[idx]


def generate_issue_motif(title: str, labels: Iterable[str]) -> str:
    """Generate a short creative motif for an issue.

    The output is deterministic: the same title/labels combination will always yield
    the same motif. This keeps logs stable and avoids surprising diffs.
    """
    theme_key = _select_theme(labels)
    theme = _THEMES[theme_key]
    seed = sum(ord(ch) for ch in title.strip().lower()) or 1

    opening = _index_for_sequence(theme["openings"], seed)
    middle = _index_for_sequence(theme["middles"], seed, 1)
    closure = _index_for_sequence(theme["closures"], seed, 2)

    motif = "\n".join([opening, middle, closure])

    if _DEBUG_ENABLED:
        logger.debug("🐛 Creative motif generated | theme=%s | seed=%s | title=%r", theme_key, seed, title)
        logger.debug("🔍 Motif lines: %s", motif.replace("\n", " | "))

    return motif


__all__ = ["generate_issue_motif"]
