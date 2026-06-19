"""Plain-language first-encounter guide for FoxClaw."""
from __future__ import annotations

from datetime import UTC, datetime


def build_visitor_guide(*, generated_at: datetime | None = None) -> dict:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0)
    return {
        "schema_version": "foxclaw_visitor_guide.v0",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "title": "FoxClaw First Encounter",
        "one_line": "FoxClaw helps people avoid turning good information into bad decisions.",
        "not_a_pitch": True,
        "audience": "curious non-traders, family, builders, and traders",
        "order": ["FoxClaw", "CoinFox", "Planifier"],
        "sections": [
            {
                "name": "FoxClaw",
                "status": "working foundation",
                "plain_language": (
                    "FoxClaw is the judgment layer. It looks at public information, checks "
                    "evidence, keeps receipts, and stays paper-only."
                ),
                "what_to_notice": [
                    "It can be quiet instead of forcing a trade.",
                    "It separates attention from evidence.",
                    "It separates a signal from a trade.",
                ],
            },
            {
                "name": "CoinFox",
                "status": "bones exist, full social product needs major work",
                "plain_language": (
                    "CoinFox already has the bones of a social trading product. The bigger "
                    "goal is to make it feel like a familiar social place for traders: "
                    "people posting trade ideas, asking questions, discussing markets, "
                    "following ideas over time, upvoting posts and comments, and branching "
                    "conversations in a fluid feed. FoxClaw intelligence can appear there "
                    "as readable context."
                ),
                "what_to_notice": [
                    "It should feel like a real social product people already understand.",
                    "Discussion is open-ended, not locked to rigid trade cards.",
                    "Long-running calls can be followed as they play out.",
                    "Strong calls and useful discussion can be spotlighted.",
                    "A popular idea is not automatically true.",
                    "A good thesis can still be a bad trade right now.",
                    "Risk labels should be honest, not hype."
                ],
            },
            {
                "name": "Planifier",
                "status": "already built, needs work",
                "plain_language": (
                    "Planifier is the planning layer. It already exists, and the next work "
                    "is connecting it cleanly so a person can turn information into a plan."
                ),
                "what_to_notice": [
                    "The user still has to choose and behave.",
                    "Plans need invalidation, sizing, and a journal.",
                    "This is decision support, not a copy-trade button.",
                ],
            },
        ],
        "safety": [
            "paper-only",
            "no live orders",
            "no funds movement",
            "no private data in the public demo",
            "no popularity-as-truth",
        ],
    }


def render_visitor_guide_markdown(guide: dict) -> str:
    lines = [
        f"# {guide['title']}",
        "",
        guide["one_line"],
        "",
        "This is not a pitch. It is a first look at the direction of the system.",
        "",
        "## The Three-Part Shape",
        "",
        " -> ".join(guide["order"]),
        "",
    ]
    for section in guide["sections"]:
        lines.extend(
            [
                f"## {section['name']}",
                "",
                f"Status: `{section['status']}`",
                "",
                section["plain_language"],
                "",
                "What to notice:",
            ]
        )
        lines.extend(f"- {item}" for item in section["what_to_notice"])
        lines.append("")
    lines.extend(["## Safety Rails", ""])
    lines.extend(f"- {item}" for item in guide["safety"])
    lines.extend(
        [
            "",
            "## The Short Version",
            "",
            "FoxClaw judges information. CoinFox is becoming the social place where "
            "traders discuss it. Planifier helps the person make a plan.",
        ]
    )
    return "\n".join(lines)
