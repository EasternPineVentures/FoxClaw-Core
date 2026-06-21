from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from foxclaw.adapters.market.signals.legacy_v13 import parse_raw_source_event

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "parser_v1"

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"source_hash_", re.I),
    re.compile(r"message_ref_hash", re.I),
    re.compile(r"private_source_ref", re.I),
    re.compile(r"private_lineage", re.I),
    re.compile(r"dedupe_key", re.I),
    re.compile(r"sanitized_message", re.I),
    re.compile(r"BTC long entry 65000", re.I),
    re.compile(r"ETH long entry 3200", re.I),
    re.compile(r"Ignore previous instructions", re.I),
    re.compile(r"USER_TOKEN", re.I),
    re.compile(r"NORMAL_USER_TOKEN", re.I),
    re.compile(r"discord(?:app)?\.com/channels", re.I),
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"discord(?:app)?\.com/channels", re.I),
    re.compile(r"discord\.gg/", re.I),
    re.compile(r"\b(?:user|channel|server|guild|message)_id\s*[:=]?\s*\d{5,}", re.I),
    re.compile(r"<[@#]!?\d{5,}>", re.I),
    re.compile(r"\b(?:token|secret|api[_-]?key|password)\s*[:=]", re.I),
    re.compile(r"\b(?:sk-[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]+)\b", re.I),
)


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_private_lineage_is_internal_but_not_reported():
    result = parse_raw_source_event(_fixture("accepted_btc_long.json"), mode="fixture")
    assert result.private_lineage["private_source_ref"]["source_ref_id"] == "source_hash_alpha"
    assert result.private_lineage["message_lineage"]["message_ref_hash"]

    report_text = json.dumps(result.to_report_dict(fixture_id="accepted_btc_long"), sort_keys=True)
    for pattern in FORBIDDEN_REPORT_PATTERNS:
        assert not pattern.search(report_text), pattern.pattern


def test_parser_cli_outputs_do_not_expose_private_lineage_or_raw_message_text():
    completed = subprocess.run(
        [
            sys.executable,
            "tools/replay_parser_compat.py",
            "--fixtures-dir",
            str(FIXTURE_DIR),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    for pattern in FORBIDDEN_REPORT_PATTERNS:
        assert not pattern.search(completed.stdout), pattern.pattern


def test_committed_parser_v1_fixtures_hide_private_discord_and_token_patterns():
    for fixture_path in FIXTURE_DIR.glob("*.json"):
        text = fixture_path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_FIXTURE_PATTERNS:
            assert not pattern.search(text), f"{fixture_path.name} contains {pattern.pattern}"


def test_parser_compat_tools_do_not_import_network_db_or_live_authority_modules():
    tool_text = "\n".join(
        [
            (REPO / "tools" / "replay_parser_compat.py").read_text(encoding="utf-8"),
            (REPO / "tools" / "compare_parser_parity.py").read_text(encoding="utf-8"),
            (REPO / "tools" / "validate_parser_legacy_results.py").read_text(encoding="utf-8"),
        ]
    )
    forbidden = (
        "sqlite3",
        "requests",
        "urllib",
        "webhook",
        "AcceptedCandidateStore",
        "RawEventStore",
        "ParseAttemptStore",
    )
    for token in forbidden:
        assert token not in tool_text
    assert "os.environ" not in tool_text
