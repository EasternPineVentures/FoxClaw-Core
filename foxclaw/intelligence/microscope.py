"""Private, read-only Microscope assessment pipeline."""
from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
from typing import Any, Mapping

from foxclaw.adapters.market.candidate_projection import (
    CandidateProjection,
    CandidateProjectionError,
    PROJECTION_VERSION,
    project_candidate,
    projection_to_dict,
)
from foxclaw.adapters.market.scoreboard import clean_rows, observations_by_subject
from foxclaw.adapters.market.setup import setup_key
from foxclaw.engine import gate, score
from foxclaw.engine.edge import BayesianEdge
from foxclaw.engine.information_quality import InformationQualityInput, assess_information_quality
from foxclaw.engine.readiness import ReadinessInput, assess_trade_readiness
from foxclaw.policy.publication import INTERNAL_ONLY, evaluate_publication
from foxclaw.store.candidate_reader import ReadOnlyCandidateReader
from foxclaw.store.market_evidence_reader import ReadOnlyMarketEvidenceReader

MICROSCOPE_ASSESSMENT_VERSION = "microscope_assessment.v0.1"
MIN_EDGE_OBSERVATIONS = score.MIN_SAMPLE_LIGHT


class MicroscopeError(RuntimeError):
    """Base error for private Microscope assessment failures."""


class MicroscopeCandidateNotFoundError(MicroscopeError):
    """Raised when the requested accepted candidate is absent."""


def assess_candidate(
    *,
    candidate_id: int,
    db_path: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a private, paper-only Microscope assessment for one accepted candidate."""
    candidate = ReadOnlyCandidateReader(db_path).get_candidate(int(candidate_id))
    if candidate is None:
        raise MicroscopeCandidateNotFoundError(f"accepted candidate {candidate_id} not found")

    projection = project_candidate(candidate)
    edge_result = _assess_edge(db_path, projection)
    information_quality = assess_information_quality(
        InformationQualityInput(
            source_independence=0,
            traceability=0,
            freshness=0,
            corroboration=0,
            contradiction_penalty=0,
        )
    )
    readiness = assess_trade_readiness(
        ReadinessInput(
            attention=0,
            evidence_quality=information_quality.evidence_quality,
            signal_confidence=0,
            cost_adjusted_edge=0,
            tradeability=0,
            entry_quality=0,
            risk=0,
            plan_readiness=0,
            source_track_record=0,
            setup_track_record=0,
        )
    )
    publication = evaluate_publication(
        {
            "publication_class": INTERNAL_ONLY,
            "claim": projection.summary or "",
            "source_classification": "internal",
            "verification_status": "unknown",
            "presentation": "qualified",
            "contains_private_source_content": False,
        },
        requested_class=INTERNAL_ONLY,
    )
    identity = {
        "assessment_version": MICROSCOPE_ASSESSMENT_VERSION,
        "projection_version": PROJECTION_VERSION,
        "candidate": {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_uid": candidate.get("candidate_uid"),
            "evidence_hash": candidate.get("evidence_hash"),
            "parser_version": candidate.get("parser_version"),
            "payload": candidate.get("normalized_payload_json"),
        },
        "edge_snapshot": edge_result["identity_snapshot"],
    }
    paper_ready = bool(
        readiness.plan_readiness == "PAPER_READY" and readiness.can_present_as_trade_idea
    )
    return {
        "assessment_version": MICROSCOPE_ASSESSMENT_VERSION,
        "assessment_id": _assessment_id(identity),
        "generated_at": generated_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "paper_only": True,
        "published": False,
        "public_card": None,
        "live_ready": False,
        "paper_ready": paper_ready,
        "candidate": {
            "internal": {
                "candidate_id": candidate.get("candidate_id"),
                "candidate_uid": candidate.get("candidate_uid"),
                "receipt_id": candidate.get("receipt_id"),
                "event_id": candidate.get("event_id"),
                "attempt_id": candidate.get("attempt_id"),
                "source_id": candidate.get("source_id"),
                "source_type": candidate.get("source_type"),
                "evidence_hash": candidate.get("evidence_hash"),
            },
            "parser_confidence": candidate.get("confidence"),
            "parser_version": candidate.get("parser_version"),
        },
        "projection": projection_to_dict(projection),
        "information_quality": asdict(information_quality),
        "readiness": asdict(readiness),
        "edge": edge_result["edge"],
        "gate": edge_result["gate"],
        "publication": {
            "publication_class": publication.publication_class,
            "allowed": publication.allowed,
            "reason_codes": list(publication.reason_codes),
            "requested_class": publication.requested_class,
            "contains_private_source_content": publication.contains_private_source_content,
            "authority": publication.authority,
        },
        "warnings": edge_result["warnings"],
    }


def _assess_edge(db_path: str, projection: CandidateProjection) -> dict[str, Any]:
    source_id = projection.internal_lineage.get("source_id")
    symbol = projection.symbol
    side = projection.side
    if not source_id or not symbol or not side:
        return _unavailable_edge(
            reason="insufficient_projection",
            observation_count=0,
            identity_snapshot={"status": "insufficient_projection"},
        )

    key = setup_key(str(source_id), str(symbol), str(side))
    rows = ReadOnlyMarketEvidenceReader(db_path).get_closed_outcomes_with_source()
    kept, filtered = clean_rows(rows)
    observations = observations_by_subject(kept).get(key, [])
    observation_count = len(observations)
    snapshot = {
        "subject": key,
        "observation_count": observation_count,
        "filtered": filtered,
        "matched_rows_hash": _matched_rows_hash(kept, key),
    }
    if observation_count < MIN_EDGE_OBSERVATIONS:
        return _unavailable_edge(
            reason="insufficient_history",
            observation_count=observation_count,
            identity_snapshot=snapshot,
            gate_reason=f"insufficient_history n={observation_count} min_n={MIN_EDGE_OBSERVATIONS}",
        )

    edge = BayesianEdge(key)
    edge.add_many(observations)
    edge_verdict = edge.verdict()
    record = _score_record(kept, key)
    gate_verdict = gate.evaluate(key, 1.0, record)
    return {
        "edge": {
            "available": True,
            "reason": "bayesian_edge_from_qualifying_outcomes",
            "observation_count": observation_count,
            "minimum_observations": MIN_EDGE_OBSERVATIONS,
            "verdict": asdict(edge_verdict),
        },
        "gate": asdict(gate_verdict),
        "warnings": [],
        "identity_snapshot": snapshot,
    }


def _unavailable_edge(
    *,
    reason: str,
    observation_count: int,
    identity_snapshot: Mapping[str, Any],
    gate_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "edge": {
            "available": False,
            "reason": reason,
            "observation_count": observation_count,
            "minimum_observations": MIN_EDGE_OBSERVATIONS,
            "verdict": None,
        },
        "gate": {
            "subject": None,
            "tier": "observe",
            "multiplier": 0.0,
            "raw_commitment": 0.0,
            "adjusted_commitment": 0.0,
            "reason": gate_reason or reason,
            "score": None,
            "n": observation_count,
            "trust_tier": "no_data",
        },
        "warnings": [reason],
        "identity_snapshot": dict(identity_snapshot),
    }


def _score_record(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    matched = [row for row in rows if _row_key(row) == key and row.get("_return") is not None]
    if not matched:
        return None
    returns = [float(row["_return"]) for row in matched]
    n = len(returns)
    wins = sum(1 for value in returns if value > 0)
    ret_pos = sum(value for value in returns if value > 0)
    ret_neg = sum(value for value in returns if value < 0)
    mean_reward = sum(returns) / n
    neg_abs = abs(ret_neg)
    if neg_abs > 0:
        reward_factor = min(ret_pos / neg_abs, 99.0)
    elif ret_pos > 0:
        reward_factor = 99.0
    else:
        reward_factor = 0.0
    success_rate = wins / n
    composite = score.composite_score(success_rate, reward_factor, n)
    return {
        "decision": score.decision_tier(composite, n, mean_reward),
        "score": composite,
        "trades": n,
        "trust_tier": score.trust_tier(n),
    }


def _row_key(row: Mapping[str, Any]) -> str:
    return setup_key(str(row.get("source_id")), str(row.get("symbol")), str(row.get("side")))


def _matched_rows_hash(rows: list[dict[str, Any]], key: str) -> str:
    matched = [
        {
            "source_id": row.get("source_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_price": row.get("entry_price"),
            "exit_price": row.get("exit_price"),
            "exit_time": row.get("exit_time"),
            "pnl_usd": row.get("pnl_usd"),
        }
        for row in rows
        if _row_key(row) == key and row.get("_return") is not None
    ]
    return "sha256:" + hashlib.sha256(_canonical_json(matched).encode("utf-8")).hexdigest()


def _assessment_id(identity: Mapping[str, Any]) -> str:
    payload = "foxclaw.microscope.assessment\n" + _canonical_json(identity)
    return "microscope_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
