"""Render public intelligence card fixtures for demo rehearsal."""
from __future__ import annotations

from html import escape
from typing import Any


def render_public_intelligence_card_markdown(card: dict[str, Any]) -> str:
    """Render a public card as concise Markdown for a human demo."""
    claim = card["claim"]
    scores = card["scores"]
    risk = card["risk_classification"]
    evidence = card["evidence"]
    attention = card["attention"]
    tradeability = card["tradeability"]

    lines = [
        "# Public Intelligence Card",
        "",
        f"ID: `{card['public_intelligence_id']}`",
        f"Mode: `{card['mode']}`",
        "",
        "## Claim",
        "",
        _safe_text(claim["summary"]),
        "",
        f"- Subject: `{_safe_text(claim['subject'])}`",
        f"- Direction / outcome: `{_safe_text(claim['direction_or_outcome'])}`",
        f"- Time horizon: `{_safe_text(claim['time_horizon'])}`",
        "",
        "## Scores",
        "",
        f"- Attention: `{scores['attention']}`",
        f"- Evidence quality: `{scores['evidence_quality']}`",
        f"- Signal confidence: `{scores['signal_confidence']}`",
        f"- Edge: `{scores['edge']}`",
        f"- Tradeability: `{scores['tradeability']}`",
        f"- Risk: `{scores['risk']}`",
        f"- Plan readiness: `{scores['plan_readiness']}`",
        "",
        "## Risk",
        "",
        f"- Class: `{_safe_text(risk['class'])}`",
        f"- Beginner safe: `{str(risk['beginner_safe']).lower()}`",
        f"- Summary: {_safe_text(risk.get('summary', ''))}",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- Supporting: {_safe_text(item)}" for item in evidence["supporting"])
    lines.extend(f"- Opposing: {_safe_text(item)}" for item in evidence["opposing"])
    lines.extend(
        [
            "",
            "## Attention",
            "",
            f"- Trend: `{_safe_text(attention['trend'])}`",
            f"- Summary: {_safe_text(attention['summary'])}",
            "",
            "## Tradeability",
            "",
            f"- Status: `{_safe_text(tradeability['status'])}`",
            f"- Summary: {_safe_text(tradeability['summary'])}",
            "",
            "## Invalidation",
            "",
            _safe_text(card["invalidation"]["summary"]),
            "",
            "## What A Professional Would Wait For",
            "",
            _safe_text(card["professional_wait_for"]),
            "",
            "## Authority",
            "",
            f"- Validation: `{_safe_text(card['status']['validation'])}`",
            f"- Publication: `{_safe_text(card['status']['publication'])}`",
            f"- Authority: `{_safe_text(card['status']['authority'])}`",
        ]
    )
    return "\n".join(lines)


def _safe_text(value: Any) -> str:
    """Escape public text before rendering it into Markdown."""
    text = str(value).replace("`", "'")
    text = " ".join(text.split())
    return escape(text, quote=False)
