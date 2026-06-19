"""Private-source and injection rules for public-boundary checks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class SourceViolation:
    reason_code: str
    field_path: str
    fragment: str


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private_message_link",
        re.compile(r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/\d+/\d+/\d+", re.I),
    ),
    ("discord_invite_link", re.compile(r"(?:discord\.gg/|discord(?:app)?\.com/invite/)", re.I)),
    ("discord_user_identifier", re.compile(r"(?:<@!?\d{5,}>|\buser_id\s*[:=]\s*\d{5,})", re.I)),
    ("discord_channel_identifier", re.compile(r"(?:<#\d{5,}>|\bchannel_id\s*[:=]\s*\d{5,})", re.I)),
    (
        "discord_server_identifier",
        re.compile(r"\b(?:server_id|guild_id)\s*[:=]\s*\d{5,}", re.I),
    ),
    (
        "credential_or_token",
        re.compile(
            r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{6,}|"
            r"(?:sk-[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]+)",
            re.I,
        ),
    ),
    (
        "prompt_injection_fragment",
        re.compile(
            r"(?:ignore (?:all )?(?:previous|prior) instructions|system prompt|developer message|"
            r"reveal (?:the )?secrets?|jailbreak|prompt injection)",
            re.I,
        ),
    ),
    (
        "html_markdown_injection",
        re.compile(
            r"(?:<\s*(?:script|iframe|img)\b|onerror\s*=|javascript:|data:text/html|\]\(\s*javascript:)",
            re.I,
        ),
    ),
    (
        "unsupported_performance_claim",
        re.compile(
            r"(?:guaranteed profit|risk[- ]?free|100%\s+win(?:rate| rate)|never loses|can't lose|sure thing)",
            re.I,
        ),
    ),
    (
        "nonpublic_source_name",
        re.compile(r"(?:private discord|closed server|members-only room|paid signal room|nonpublic source)", re.I),
    ),
)

_RAW_QUOTE_FIELD_NAMES = {
    "raw_discord_quote",
    "raw_private_quote",
    "message_content",
    "raw_message",
    "discord_message",
}


def scan_text(value: str, *, field_path: str = "$") -> tuple[SourceViolation, ...]:
    """Return source/privacy/injection violations found in one text value."""
    text = str(value or "")
    violations: list[SourceViolation] = []
    for reason_code, pattern in _PATTERNS:
        match = pattern.search(text)
        if match:
            violations.append(
                SourceViolation(reason_code, field_path, _fragment(text, match.start(), match.end()))
            )
    if _looks_like_raw_discord_quote(text) or _raw_quote_field(field_path):
        violations.append(SourceViolation("raw_private_discord_quotation", field_path, _fragment(text, 0, 80)))
    return tuple(violations)


def scan_payload_strings(payload: Mapping[str, Any]) -> tuple[SourceViolation, ...]:
    """Scan all string values in a nested payload."""
    return tuple(_walk_strings(payload, "$"))


def reason_codes(violations: Iterable[SourceViolation]) -> tuple[str, ...]:
    """Return stable unique reason codes from violations."""
    seen: set[str] = set()
    out: list[str] = []
    for violation in violations:
        if violation.reason_code not in seen:
            seen.add(violation.reason_code)
            out.append(violation.reason_code)
    return tuple(out)


def _walk_strings(value: Any, path: str) -> Iterable[SourceViolation]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}")
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield from scan_text(value, field_path=path)


def _looks_like_raw_discord_quote(text: str) -> bool:
    lowered = text.lower()
    return (
        (" today at " in lowered or " yesterday at " in lowered)
        and ("@" in text or ":" in text)
        and len(text.split()) >= 4
    )


def _raw_quote_field(field_path: str) -> bool:
    field = field_path.rsplit(".", maxsplit=1)[-1].lower()
    return field in _RAW_QUOTE_FIELD_NAMES


def _fragment(text: str, start: int, end: int) -> str:
    left = max(0, start - 24)
    right = min(len(text), end + 24)
    return " ".join(text[left:right].split())[:120]
