#!/usr/bin/env python3
"""Structural invariant guards — make the doctrine a rail, not just a document.

Design principle: **a guard that flags legitimate code is worse than no guard** — it
trains people to ignore it, or it cripples real work. So every check here is scoped to
where the code is *actually* meant to be clean, and skips strings/comments so docstrings
can speak plainly. Checks that can't yet be done without false positives are deliberately
left OFF and documented, not shipped half-broken.

Enforced now (all green at v0.1.x):
  #6  pure-stdlib core   — foxclaw/{engine,store,policy} import only stdlib + foxclaw.
  #4  domain-neutral     — foxclaw/engine/ uses no market vocabulary (identifiers only;
                           strings/comments are exempt). Scoped to engine ONLY, because
                           store/ legitimately carries PnL/sharpe (pin P1 decides if/when
                           that moves). Expand to store/ once P1 is resolved.
  #9  per-node store      — *.db and data/ are gitignored; no .db file is tracked.

Deliberately NOT enforced yet (would false-positive — see pin discipline):
  #1  paper-only         — a naive grep for live_trade/fund_move flags decision_policy.py
                           and journal.py, which legitimately *list* those as BLOCKED. A
                           real check must understand "names a term to forbid it" vs
                           "performs it". Left for a designed AST check, not a grep.

Usage:  python tools/check_invariants.py          # exit 0 clean, 1 on any violation
        python tools/check_invariants.py --quiet  # only print failures
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "foxclaw"

# Always-allowed import roots beyond the stdlib.
ALLOWED_IMPORT_ROOTS = {"foxclaw", "__future__"}

# #6 scope: the core packages that must stay pure-stdlib (sqlite3/json/hashlib are stdlib).
PURE_STDLIB_DIRS = ("engine", "store", "policy")

# #4 scope: ENGINE ONLY for now (store/ has market vocab by necessity until P1).
DOMAIN_NEUTRAL_DIRS = ("engine",)

# #4 forbidden identifiers (lowercased NAME tokens). Conservative + market-unambiguous,
# so neutral decision math (arm/reward/cost/success) is never tripped. Tune here.
MARKET_TERMS = {
    "pnl", "realized_pnl", "realized_pnl_usd", "unrealized_pnl",
    "win_rate", "profit_factor", "sharpe", "drawdown",
    "symbol", "ticker", "ohlcv", "candle", "venue",
    "long", "short", "buy", "sell",
}


def _py_files(*subdirs: str) -> list[Path]:
    out: list[Path] = []
    for sub in subdirs:
        base = PKG / sub
        if base.exists():
            out.extend(sorted(base.rglob("*.py")))
    return out


def check_pure_stdlib() -> list[str]:
    """#6 — core packages may import only the standard library and foxclaw itself."""
    stdlib = sys.stdlib_module_names  # Python 3.10+
    violations: list[str] = []
    for path in _py_files(*PURE_STDLIB_DIRS):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover
            violations.append(f"{path.relative_to(REPO)}: syntax error: {exc}")
            continue
        for node in ast.walk(tree):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative intra-package import
                roots = [(node.module or "").split(".")[0]]
            for root in roots:
                if not root or root in ALLOWED_IMPORT_ROOTS or root in stdlib:
                    continue
                violations.append(
                    f"{path.relative_to(REPO)}:{node.lineno}: non-stdlib import '{root}' "
                    f"(invariant #6: core stays pure stdlib)"
                )
    return violations


def check_domain_neutral() -> list[str]:
    """#4 — engine/ uses no market vocabulary as identifiers (strings/comments exempt)."""
    violations: list[str] = []
    for path in _py_files(*DOMAIN_NEUTRAL_DIRS):
        with path.open("rb") as fh:
            try:
                for tok in tokenize.tokenize(fh.readline):
                    if tok.type == tokenize.NAME and tok.string.lower() in MARKET_TERMS:
                        violations.append(
                            f"{path.relative_to(REPO)}:{tok.start[0]}: market term "
                            f"'{tok.string}' in engine/ (invariant #4: domain-neutral core)"
                        )
            except tokenize.TokenError as exc:  # pragma: no cover
                violations.append(f"{path.relative_to(REPO)}: tokenize error: {exc}")
    return violations


def check_per_node_store() -> list[str]:
    """#9 — *.db and data/ are gitignored, and no .db file is tracked in git."""
    violations: list[str] = []
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8") if (REPO / ".gitignore").exists() else ""
    for pattern in ("*.db", "data/"):
        if pattern not in gitignore:
            violations.append(f".gitignore: missing '{pattern}' (invariant #9: per-node store)")
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        for f in tracked:
            if f.endswith((".db", ".db-wal", ".db-shm")):
                violations.append(f"{f}: database file is tracked (invariant #9: never commit a node DB)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # git unavailable — skip the tracked-file check, keep the .gitignore check
    return violations


CHECKS = (
    ("#6 pure-stdlib core   (engine/store/policy)", check_pure_stdlib),
    ("#4 domain-neutral core (engine/ only)", check_domain_neutral),
    ("#9 per-node store      (db gitignored/untracked)", check_per_node_store),
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    args = ap.parse_args()

    total = 0
    for label, fn in CHECKS:
        violations = fn()
        total += len(violations)
        if violations:
            print(f"[FAIL] {label}")
            for v in violations:
                print(f"       {v}")
        elif not args.quiet:
            print(f"[ok]   {label}")

    if total:
        print(f"\n{total} invariant violation(s).")
        return 1
    if not args.quiet:
        print("\nAll structural invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
