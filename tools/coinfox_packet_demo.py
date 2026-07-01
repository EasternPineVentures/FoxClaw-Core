#!/usr/bin/env python3
"""Render a public-safe FoxClaw-to-CoinFox curated packet fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.public.coinfox_packet import render_coinfox_curated_packet_markdown  # noqa: E402
from foxclaw.security.packet_trust_metadata import (  # noqa: E402
    build_packet_trust_metadata,
    render_packet_trust_metadata_markdown,
)
from foxclaw.security.prompt_injection import scan as scan_prompt_injection  # noqa: E402
from foxclaw.security.quarantine import default_source_state, quarantine_decision  # noqa: E402
from foxclaw.security.source_registry import get_source_policy  # noqa: E402

DEFAULT_FIXTURE = REPO / "tests" / "fixtures" / "public_contract" / "coinfox_curated_packet.valid.json"
SCAN_FIELDS = ("text", "content", "summary", "public_safe_summary")


def guard_coinfox_packet_intake(payload: dict[str, Any]) -> dict[str, object] | None:
    """Return a public-safe quarantine error if raw intake cannot create a packet."""
    return evaluate_coinfox_packet_intake(payload)["blocked"]


def evaluate_coinfox_packet_intake(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate raw intake and return the quarantine result plus trust metadata."""
    metadata: list[dict[str, object]] = []
    for observation, fallback_state in _iter_observations(payload):
        source_state = _source_state_for(observation, fallback_state)
        scan_result = scan_prompt_injection(_scan_text(observation))
        corroboration_count = _corroboration_count(observation)
        decision = quarantine_decision(
            observation=observation,
            source_state=source_state,
            corroboration_count=corroboration_count,
            prompt_injection_flagged=bool(scan_result["flagged"]),
        )
        metadata.append(
            build_packet_trust_metadata(
                observation=observation,
                source_state=source_state,
                scan_result=scan_result,
                decision=decision,
                corroboration_count=corroboration_count,
            )
        )
        if not decision["allowed"]:
            return {
                "blocked": {
                    "error": "quarantined",
                    "reason": decision["reason"],
                    "next_steps": decision["next_steps"],
                },
                "trust_metadata": metadata,
            }
    return {"blocked": None, "trust_metadata": metadata}


def _blocked_output(
    blocked: dict[str, object],
    trust_metadata: list[dict[str, object]],
    *,
    include_trust_metadata: bool,
) -> dict[str, object]:
    if not include_trust_metadata:
        return blocked
    return {
        **blocked,
        "trust_metadata": trust_metadata,
    }


def _iter_observations(payload: dict[str, Any]):
    fallback_state = payload.get("source_state") if isinstance(payload.get("source_state"), dict) else None
    observations = payload.get("source_observations")
    if isinstance(observations, list):
        for observation in observations:
            if isinstance(observation, dict):
                yield observation, fallback_state
        return
    observation = payload.get("observation")
    if isinstance(observation, dict):
        yield observation, fallback_state
        return
    yield payload, fallback_state


def _source_state_for(
    observation: dict[str, Any],
    fallback_state: dict[str, Any] | None,
) -> dict[str, object]:
    source_id = _source_id_for(observation)
    if source_id is not None:
        return get_source_policy(source_id)
    if isinstance(observation.get("source_state"), dict):
        return dict(observation["source_state"])
    if fallback_state is not None:
        return dict(fallback_state)

    source = observation.get("source")
    source = source if isinstance(source, dict) else {}
    fallback_source_id = source.get("source_name") or observation.get("observation_id") or "unknown_source"
    source_type = source.get("source_type") or observation.get("source_type") or "unknown"
    return default_source_state(str(fallback_source_id), str(source_type))


def _source_id_for(observation: dict[str, Any]) -> str | None:
    source = observation.get("source")
    source = source if isinstance(source, dict) else {}
    source_id = source.get("source_id") or observation.get("source_id")
    if source_id is None:
        return None
    source_id_text = str(source_id).strip()
    return source_id_text or None


def _corroboration_count(observation: dict[str, Any]) -> int:
    corroborations = observation.get("corroborations", [])
    return len(corroborations) if isinstance(corroborations, list) else 0


def _scan_text(observation: dict[str, Any]) -> str:
    parts = [observation[field] for field in SCAN_FIELDS if isinstance(observation.get(field), str)]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", default=str(DEFAULT_FIXTURE), help="curated packet JSON path")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use the checked-in curated packet fixture; kept for command symmetry",
    )
    parser.add_argument(
        "--intake",
        help="optional raw intake/observation JSON path to quarantine-check before rendering",
    )
    parser.add_argument(
        "--trust-metadata",
        action="store_true",
        help="emit sanitized Packet Trust Metadata V0 for evaluated intake",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    trust_metadata: list[dict[str, object]] = []
    if args.intake:
        intake_payload = json.loads(Path(args.intake).read_text(encoding="utf-8"))
        evaluated = evaluate_coinfox_packet_intake(intake_payload)
        blocked = evaluated["blocked"]
        trust_metadata = evaluated["trust_metadata"]
        if blocked is not None:
            print(
                json.dumps(
                    _blocked_output(
                        blocked,
                        trust_metadata,
                        include_trust_metadata=args.trust_metadata,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 2

    packet_path = DEFAULT_FIXTURE if args.fixture else Path(args.packet)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if args.json:
        output: dict[str, Any] = packet
        if args.trust_metadata:
            output = {
                "packet": packet,
                "trust_metadata": trust_metadata,
            }
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(render_coinfox_curated_packet_markdown(packet))
        if args.trust_metadata:
            print()
            print(render_packet_trust_metadata_markdown(trust_metadata))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
