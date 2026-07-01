"""Render public-safe FoxClaw-to-CoinFox curated packets."""
from __future__ import annotations

from typing import Any


def render_coinfox_curated_packet_markdown(packet: dict[str, Any]) -> str:
    """Render a curated packet as plain Markdown for review/demo use."""
    lines = [
        "# CoinFox Curated Packet",
        "",
        f"Packet: `{packet['packet_id']}`",
        f"Type: `{packet['packet_type']}`",
        f"Mode: `{packet['mode']}`",
        "",
        packet["disclosure"],
        "",
        "## Source Window",
        "",
        f"- Started: `{packet['source_window']['started_at']}`",
        f"- Ended: `{packet['source_window']['ended_at']}`",
        f"- Summary: {packet['source_window']['summary']}",
        f"- Private lineage excluded: `{str(packet['source_window']['private_lineage_excluded']).lower()}`",
        "",
        "## Cards",
        "",
    ]
    for card in packet["cards"]:
        lines.extend(
            [
                f"### {card['title']}",
                "",
                f"- Card ID: `{card['card_id']}`",
                f"- Type: `{card['card_type']}`",
                f"- Asset / topic: `{card['asset_or_topic']}`",
                f"- Status: `{card['card_status']}`",
                f"- Confidence: `{card['confidence']}`",
                f"- Source quality: `{card['source_quality']['display_label']}` "
                f"({card['source_quality']['confidence_score']}/100)",
                f"- Tags: {', '.join(f'`{tag}`' for tag in card['tags'])}",
                "",
                f"Why interesting: {card['why_interesting']}",
                "",
                f"Public-safe summary: {card['public_safe_summary']}",
                "",
                f"Counterpoint: {card['counterpoint']}",
                "",
                f"Suggested thesis angle: {card['suggested_thesis_angle']}",
                "",
                f"CoinFox prompt: {card['suggested_coinfox_prompt']}",
                "",
                "Sources:",
            ]
        )
        for source in card["source_links"]:
            lines.append(
                f"- [{source['source_name']}]({source['source_url']}) "
                f"`{source['source_type']}`"
            )
        lines.extend(
            [
                "",
                "Outcome memory:",
                f"- Status: `{card['outcome_memory']['outcome_status']}`",
                f"- Review after: `{card['outcome_memory']['review_after']}`",
                f"- Review question: {card['outcome_memory']['review_question']}",
                "",
                "Safety:",
                f"- Authority: `{card['safety']['authority']}`",
                f"- Raw content included: `{str(card['safety']['raw_content_included']).lower()}`",
                f"- Private source content: `{str(card['safety']['contains_private_source_content']).lower()}`",
                f"- Live execution allowed: `{str(card['safety']['live_execution_allowed']).lower()}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Packet Authority",
            "",
            f"- Authority: `{packet['status']['authority']}`",
            f"- Can submit order: `{str(packet['status']['can_submit_order']).lower()}`",
            f"- Can move funds: `{str(packet['status']['can_move_funds']).lower()}`",
            f"- Live execution allowed: `{str(packet['status']['live_execution_allowed']).lower()}`",
        ]
    )
    return "\n".join(lines)
