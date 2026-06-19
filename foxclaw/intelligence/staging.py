"""Safe local staging for Microscope public-contract handoff files."""
from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from foxclaw.adapters.market.candidate_projection import (
    CandidatePayloadDecodeError,
    CandidatePayloadTypeError,
    CandidateProjectionError,
)
from foxclaw.contract.public import PUBLIC_CONTRACT_VERSION, manifest as public_contract_manifest
from foxclaw.contract.public.export import DISCLOSURE, validate_public_card
from foxclaw.intelligence.microscope import (
    MICROSCOPE_ASSESSMENT_VERSION,
    MicroscopeCandidateNotFoundError,
    assess_candidate,
)
from foxclaw.store.candidate_reader import (
    CandidateDatabaseError,
    CandidateDatabaseMissingError,
    CandidateReaderError,
    CandidateSchemaError,
    ReadOnlyCandidateReader,
)

DEFAULT_STAGING_ROOT = Path("runtime_exports") / "coinfox" / "staging"
DEFAULT_CURSOR_PATH = Path("runtime_logs") / "microscope_cursor.json"
STAGING_SCHEMA_VERSION = "microscope_coinfox_staging.v0"
CURSOR_SCHEMA_VERSION = "microscope_cursor.v0"

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")


class PublicCardStagingError(RuntimeError):
    """Raised when an approved assessment cannot produce a valid public card."""


def staged_card_id(assessment: Mapping[str, Any]) -> str:
    """Return a stable public-card staging id from assessment lineage."""
    identity = {
        "assessment_id": assessment.get("assessment_id"),
        "assessment_version": assessment.get("assessment_version"),
        "contract_version": _contract_version(assessment),
    }
    digest = hashlib.sha256(
        ("foxclaw.microscope.staged_card\n" + _canonical_json(identity)).encode("utf-8")
    ).hexdigest()
    return "coinfox_card_" + digest[:32]


def public_card_for_staging(assessment: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a validated public card only after publication approval."""
    publication = assessment.get("publication")
    if not isinstance(publication, Mapping) or not bool(publication.get("allowed")):
        return None

    card = assessment.get("public_card")
    if not isinstance(card, Mapping):
        raise PublicCardStagingError("publication approved but public_card is missing")

    staged = dict(card)
    staged.setdefault("public_intelligence_id", staged_card_id(assessment))
    try:
        validate_public_card(staged)
    except ValueError as exc:
        raise PublicCardStagingError(f"public card failed validation: {exc}") from exc
    return staged


def run_microscope_batch(
    *,
    db_path: str | Path,
    after_id: int,
    limit: int,
    output_root: str | Path = DEFAULT_STAGING_ROOT,
    cursor_path: str | Path = DEFAULT_CURSOR_PATH,
    dry_run: bool = True,
    write_staging: bool = False,
    run_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Assess accepted candidates and optionally stage local CoinFox handoff files."""
    if dry_run and write_staging:
        raise ValueError("dry_run and write_staging cannot both be true")

    generated = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    selected = ReadOnlyCandidateReader(db_path).iter_after(candidate_id=after_id, limit=limit)
    safe_run_id = _safe_run_id(run_id or _default_run_id(generated))

    cards: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    assessed = 0
    last_candidate_id = int(after_id)

    for candidate in selected:
        candidate_id = int(candidate["candidate_id"])
        last_candidate_id = max(last_candidate_id, candidate_id)
        try:
            assessment = assess_candidate(
                candidate_id=candidate_id,
                db_path=str(db_path),
                generated_at=generated,
            )
            assessed += 1
            card = public_card_for_staging(assessment)
            if card is not None:
                cards.append(card)
        except _EXPECTED_BATCH_ERRORS as exc:
            failures.append(_failure_record(candidate_id, exc, generated_at=generated))

    counts = {
        "selected": len(selected),
        "assessed": assessed,
        "cards": len(cards),
        "failures": len(failures),
    }

    cursor_updated = False
    if write_staging:
        write_staging_artifacts(
            output_root=output_root,
            run_id=safe_run_id,
            cards=cards,
            failures=failures,
            counts=counts,
            generated_at=generated,
        )
        if selected and not failures:
            _write_cursor(
                cursor_path,
                {
                    "schema_version": CURSOR_SCHEMA_VERSION,
                    "last_candidate_id": last_candidate_id,
                    "run_id": safe_run_id,
                    "updated_at": generated,
                },
            )
            cursor_updated = True

    return {
        "schema_version": STAGING_SCHEMA_VERSION,
        "run_id": safe_run_id,
        "dry_run": dry_run,
        "write_staging": write_staging,
        "cursor_updated": cursor_updated,
        "contract_version": _contract_version({}),
        "counts": counts,
        "status": _status(),
        "artifacts": _artifact_names() if write_staging else [],
    }


def write_staging_artifacts(
    *,
    output_root: str | Path,
    run_id: str,
    cards: Iterable[Mapping[str, Any]],
    failures: Iterable[Mapping[str, Any]],
    counts: Mapping[str, int],
    generated_at: str,
) -> dict[str, Path]:
    """Write staging artifacts with atomic file replacement."""
    safe_run_id = _safe_run_id(run_id)
    run_dir = Path(output_root) / safe_run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    card_list = [dict(card) for card in cards]
    failure_list = [dict(failure) for failure in failures]
    cards_text = _jsonl(card_list, key="public_intelligence_id")
    failures_text = _jsonl(failure_list, key="failure_id")

    cards_path = run_dir / "cards.jsonl"
    failures_path = run_dir / "failures.jsonl"
    manifest_path = run_dir / "manifest.json"

    _atomic_write_text(cards_path, cards_text)
    _atomic_write_text(failures_path, failures_text)

    manifest = _manifest(
        run_id=safe_run_id,
        cards_text=cards_text,
        failures_text=failures_text,
        counts=counts,
        generated_at=generated_at,
    )
    _atomic_write_text(manifest_path, _json(manifest))
    return {"manifest": manifest_path, "cards": cards_path, "failures": failures_path}


def read_cursor(path: str | Path) -> int:
    """Read the internal batch cursor, returning 0 when it does not exist."""
    cursor = Path(path)
    if not cursor.exists():
        return 0
    payload = json.loads(cursor.read_text(encoding="utf-8"))
    return int(payload.get("last_candidate_id") or 0)


def _manifest(
    *,
    run_id: str,
    cards_text: str,
    failures_text: str,
    counts: Mapping[str, int],
    generated_at: str,
) -> dict[str, Any]:
    contract = _contract_info()
    return {
        "schema_version": STAGING_SCHEMA_VERSION,
        "contract_name": contract["name"],
        "contract_version": contract["version"],
        "assessment_version": MICROSCOPE_ASSESSMENT_VERSION,
        "generated_at": generated_at,
        "run_id": run_id,
        "author_type": "system",
        "author_display": "FoxClaw",
        "mode": "informational_paper",
        "disclosure": DISCLOSURE,
        "files": {
            "cards": "cards.jsonl",
            "failures": "failures.jsonl",
        },
        "hashes": {
            "cards": _sha256(cards_text),
            "failures": _sha256(failures_text),
        },
        "counts": {
            "selected": int(counts.get("selected", 0)),
            "assessed": int(counts.get("assessed", 0)),
            "cards": int(counts.get("cards", 0)),
            "failures": int(counts.get("failures", 0)),
        },
        "status": _status(),
    }


def _status() -> dict[str, bool | str]:
    return {
        "authority": "paper_only",
        "published": False,
        "coinfox_api_called": False,
        "coinfox_db_written": False,
        "live_execution_allowed": False,
        "not_individualized_advice": True,
    }


def _failure_record(candidate_id: int, exc: BaseException, *, generated_at: str) -> dict[str, Any]:
    error_code = _error_code(exc)
    digest = hashlib.sha256(
        f"foxclaw.microscope.failure\n{candidate_id}\n{error_code}".encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "microscope_failure.v0",
        "failure_id": "microscope_failure_" + digest[:24],
        "error_code": error_code,
        "message": _safe_failure_message(exc),
        "retriable": True,
        "occurred_at": generated_at,
    }


def _error_code(exc: BaseException) -> str:
    if isinstance(exc, CandidatePayloadDecodeError):
        return "candidate_payload_decode_error"
    if isinstance(exc, CandidatePayloadTypeError):
        return "candidate_payload_type_error"
    if isinstance(exc, CandidateProjectionError):
        return "candidate_projection_error"
    if isinstance(exc, MicroscopeCandidateNotFoundError):
        return "microscope_candidate_not_found"
    if isinstance(exc, PublicCardStagingError):
        return "public_card_staging_error"
    if isinstance(exc, CandidateDatabaseMissingError):
        return "candidate_database_missing_error"
    if isinstance(exc, CandidateSchemaError):
        return "candidate_schema_error"
    if isinstance(exc, CandidateDatabaseError):
        return "candidate_database_error"
    if isinstance(exc, CandidateReaderError):
        return "candidate_reader_error"
    return "microscope_batch_error"


def _safe_failure_message(exc: BaseException) -> str:
    if isinstance(exc, CandidatePayloadDecodeError):
        return "candidate payload could not be decoded"
    if isinstance(exc, CandidatePayloadTypeError):
        return "candidate payload must decode to an object"
    if isinstance(exc, CandidateProjectionError):
        return "candidate payload failed projection"
    if isinstance(exc, MicroscopeCandidateNotFoundError):
        return "candidate could not be found"
    if isinstance(exc, PublicCardStagingError):
        return str(exc)
    if isinstance(exc, CandidateReaderError):
        return "read-only candidate database query failed"
    return "microscope batch item failed"


def _contract_info() -> dict[str, str]:
    try:
        contract = public_contract_manifest()
    except (OSError, json.JSONDecodeError, TypeError):
        contract = {}
    return {
        "name": str(contract.get("contract_name") or "foxclaw-public-intelligence"),
        "version": str(contract.get("contract_version") or PUBLIC_CONTRACT_VERSION),
    }


def _contract_version(assessment: Mapping[str, Any]) -> str:
    contract = assessment.get("contract") if isinstance(assessment, Mapping) else None
    if isinstance(contract, Mapping) and contract.get("version"):
        return str(contract["version"])
    return _contract_info()["version"]


def _artifact_names() -> list[str]:
    return ["manifest.json", "cards.jsonl", "failures.jsonl"]


def _safe_run_id(value: str) -> str:
    if not _RUN_ID_RE.fullmatch(value):
        raise ValueError("run_id must use only letters, numbers, dots, hyphens, or underscores")
    return value


def _default_run_id(generated_at: str) -> str:
    stamp = re.sub(r"[^0-9A-Za-z]", "", generated_at)[:32] or "run"
    suffix = hashlib.sha256(generated_at.encode("utf-8")).hexdigest()[:8]
    return f"microscope_{stamp}_{suffix}"


def _write_cursor(path: str | Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_text(Path(path), _json(payload))


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_text(text, encoding="utf-8")
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _jsonl(values: Iterable[Mapping[str, Any]], *, key: str) -> str:
    rows = sorted(values, key=lambda item: str(item.get(key) or ""))
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


_EXPECTED_BATCH_ERRORS = (
    CandidateProjectionError,
    MicroscopeCandidateNotFoundError,
    PublicCardStagingError,
    CandidateReaderError,
)
