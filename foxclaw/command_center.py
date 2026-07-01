"""Operator command catalog for FoxClaw Core."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO / "config" / "foxclaw_commands.json"

AUTHORITY_KEYS = (
    "can_submit_order",
    "can_move_funds",
    "live_execution_allowed",
    "can_publish_to_coinfox",
    "can_change_truth",
    "can_change_source_reliability",
    "can_update_verified_memory",
    "can_train_model",
    "can_run_live_network",
)

RUNNABLE_PREFIXES = (
    "python tools\\",
    "python tools/",
    "python -m pytest",
    "git status --short --branch",
    "git diff --check",
)

UNSAFE_RUNNABLE_FRAGMENTS = (
    "--live",
    "--apply",
    "--reset-demo",
    "--secret-file",
    "--write-staging",
    "--write ",
    " submit",
    " order",
    " funds",
    " wallet",
)


def load_catalog(path: str | Path = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog_path = Path(path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != "foxclaw_commands.v0":
        raise ValueError("command catalog must use schema_version foxclaw_commands.v0")
    _validate_authority(catalog.get("authority", {}))
    groups = catalog.get("groups", [])
    if not groups:
        raise ValueError("command catalog must contain at least one group")
    seen_group_ids: set[str] = set()
    seen_command_ids: set[str] = set()
    for group in groups:
        group_id = _required_str(group, "id")
        if group_id in seen_group_ids:
            raise ValueError(f"duplicate command group id: {group_id}")
        seen_group_ids.add(group_id)
        commands = group.get("commands", [])
        if not commands:
            raise ValueError(f"command group has no commands: {group_id}")
        for command in commands:
            command_id = _required_str(command, "id")
            if command_id in seen_command_ids:
                raise ValueError(f"duplicate command id: {command_id}")
            seen_command_ids.add(command_id)
            _validate_command(command)
    return catalog


def build_report(
    path: str | Path = DEFAULT_CATALOG,
    *,
    category: str | None = None,
    search: str | None = None,
    include_all_tools: bool = False,
) -> dict[str, Any]:
    catalog = load_catalog(path)
    groups = _filter_groups(catalog["groups"], category=category, search=search)
    commands = [command for group in groups for command in group["commands"]]
    report = {
        "schema_version": "foxclaw_command_center_report.v0",
        "catalog_updated_at": catalog["updated_at"],
        "generated_for": catalog["generated_for"],
        "authority": catalog["authority"],
        "group_count": len(groups),
        "command_count": len(commands),
        "runnable_command_count": sum(1 for command in commands if command["runnable"]),
        "groups": groups,
        "all_tool_count": len(discover_tools()),
    }
    if include_all_tools:
        report["all_tools"] = discover_tools()
    return report


def flatten_commands(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {**command, "group_id": group["id"], "group_title": group["title"]}
        for group in catalog["groups"]
        for command in group["commands"]
    ]


def find_command(command_id: str, path: str | Path = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog = load_catalog(path)
    for command in flatten_commands(catalog):
        if command["id"] == command_id:
            return command
    raise KeyError(f"unknown command id: {command_id}")


def discover_tools(repo: str | Path = REPO) -> list[dict[str, str]]:
    tools_dir = Path(repo) / "tools"
    tools: list[dict[str, str]] = []
    for path in sorted(tools_dir.glob("*.py")):
        tools.append(
            {
                "name": path.name,
                "path": str(path.relative_to(repo)).replace("/", "\\"),
                "summary": _docstring_summary(path),
                "help_command": f"python tools\\{path.name} --help",
            }
        )
    return tools


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FoxClaw Command Center",
        "",
        f"Catalog updated: `{report['catalog_updated_at']}`",
        f"Curated commands: `{report['command_count']}`",
        f"Runnable safe commands: `{report['runnable_command_count']}`",
        f"Actual tool scripts found: `{report['all_tool_count']}`",
        "",
        "Run by ID:",
        "",
        "```powershell",
        "python tools\\foxclaw_commands.py --run <command-id>",
        "```",
        "",
        "Search:",
        "",
        "```powershell",
        "python tools\\foxclaw_commands.py --search packet",
        "```",
        "",
    ]
    for group in report["groups"]:
        lines.extend([f"## {group['title']}", "", group["purpose"], ""])
        for command in group["commands"]:
            runnable = "runnable" if command["runnable"] else "manual"
            lines.append(f"- `{command['id']}` ({runnable}): {command['title']}")
            lines.append(f"  `{command['command']}`")
            lines.append(f"  {command['purpose']}")
        lines.append("")
    if report.get("all_tools"):
        lines.extend(["## All Tool Scripts", ""])
        for tool in report["all_tools"]:
            lines.append(f"- `{tool['path']}`: {tool['summary']}")
            lines.append(f"  Help: `{tool['help_command']}`")
        lines.append("")
    lines.extend(
        [
            "## Authority",
            "",
            "- `can_submit_order=false`",
            "- `can_move_funds=false`",
            "- `live_execution_allowed=false`",
            "- `can_publish_to_coinfox=false`",
            "- `can_change_truth=false`",
            "- `can_change_source_reliability=false`",
            "- `can_update_verified_memory=false`",
            "- `can_train_model=false`",
            "- `can_run_live_network=false`",
            "",
        ]
    )
    return "\n".join(lines)


def render_command(command: dict[str, Any]) -> str:
    docs = ", ".join(command.get("docs", [])) or "none"
    tags = ", ".join(command.get("tags", [])) or "none"
    runnable = "yes" if command["runnable"] else "manual only"
    return "\n".join(
        [
            f"# {command['title']}",
            "",
            f"ID: `{command['id']}`",
            f"Group: `{command.get('group_title', command.get('group_id', 'unknown'))}`",
            f"Runnable: `{runnable}`",
            f"Safety: `{command['safety']}`",
            "",
            "```powershell",
            command["command"],
            "```",
            "",
            command["purpose"],
            "",
            f"When: {command['when']}",
            f"Docs: {docs}",
            f"Tags: {tags}",
            "",
        ]
    )


def run_command(command_id: str, path: str | Path = DEFAULT_CATALOG) -> int:
    command = find_command(command_id, path)
    if not command["runnable"]:
        raise ValueError(
            f"command '{command_id}' is manual-only; copy it from --show after reviewing paths"
        )
    completed = subprocess.run(command["command"], cwd=REPO, shell=True)
    return int(completed.returncode)


def _filter_groups(
    groups: list[dict[str, Any]],
    *,
    category: str | None,
    search: str | None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    search_lower = search.lower() if search else None
    for group in groups:
        if category and group["id"] != category:
            continue
        commands = []
        for command in group["commands"]:
            if search_lower and search_lower not in _search_blob(group, command):
                continue
            commands.append(command)
        if commands:
            filtered.append({**group, "commands": commands})
    return filtered


def _search_blob(group: dict[str, Any], command: dict[str, Any]) -> str:
    parts = [
        group["id"],
        group["title"],
        group["purpose"],
        command["id"],
        command["title"],
        command["command"],
        command["purpose"],
        command["when"],
        command["safety"],
        " ".join(command.get("docs", [])),
        " ".join(command.get("tags", [])),
    ]
    return " ".join(parts).lower()


def _validate_authority(authority: dict[str, Any]) -> None:
    for key in AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"command catalog authority must keep {key}=false")


def _validate_command(command: dict[str, Any]) -> None:
    for key in (
        "id",
        "title",
        "command",
        "purpose",
        "when",
        "safety",
    ):
        _required_str(command, key)
    if not isinstance(command.get("runnable"), bool):
        raise ValueError(f"command {command.get('id', '<unknown>')} must define boolean runnable")
    if not isinstance(command.get("docs"), list):
        raise ValueError(f"command {command['id']} must define docs list")
    if not isinstance(command.get("tags"), list):
        raise ValueError(f"command {command['id']} must define tags list")
    if command["runnable"]:
        _validate_runnable_command(command["id"], command["command"])
    _validate_doc_paths(command)


def _validate_runnable_command(command_id: str, command: str) -> None:
    normalized = command.strip().lower()
    if not any(normalized.startswith(prefix) for prefix in RUNNABLE_PREFIXES):
        raise ValueError(f"runnable command {command_id} uses unsupported prefix: {command}")
    for fragment in UNSAFE_RUNNABLE_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(f"runnable command {command_id} contains unsafe fragment {fragment}")
    tool_path = _tool_path_from_command(command)
    if tool_path and not (REPO / tool_path).exists():
        raise ValueError(f"runnable command {command_id} references missing tool: {tool_path}")


def _tool_path_from_command(command: str) -> Path | None:
    parts = command.split()
    if len(parts) < 2:
        return None
    candidate = parts[1].replace("/", "\\")
    if candidate.startswith("tools\\") and candidate.endswith(".py"):
        return Path(candidate)
    return None


def _validate_doc_paths(command: dict[str, Any]) -> None:
    for raw_path in command["docs"]:
        path = REPO / str(raw_path)
        if "<" in str(raw_path) or ">" in str(raw_path):
            continue
        if not path.exists():
            raise ValueError(f"command {command['id']} references missing doc: {raw_path}")


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"command catalog item missing string field: {key}")
    return value


def _docstring_summary(path: Path) -> str:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return "No summary available."
    docstring = ast.get_docstring(module) or "No summary available."
    return " ".join(docstring.strip().split())
