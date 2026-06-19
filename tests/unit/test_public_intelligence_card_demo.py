from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.contract.public.card import render_public_intelligence_card_markdown

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "public_intelligence_card_demo.py"
FIXTURE = REPO / "tests" / "fixtures" / "public_contract" / "public_intelligence_card.valid.json"


def test_public_card_renderer_names_professional_wait_and_authority():
    card = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rendered = render_public_intelligence_card_markdown(card)
    assert "# Public Intelligence Card" in rendered
    assert "What A Professional Would Wait For" in rendered
    assert "current entry quality is poor" in rendered.lower()
    assert "- Authority: `paper_only`" in rendered
    assert "dossier_hash" not in rendered


def test_public_card_demo_cli_fixture_renders_markdown():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Public Intelligence Card" in completed.stdout
    assert "Attention" in completed.stdout
    assert "Tradeability" in completed.stdout
    assert "Beginner safe: `false`" in completed.stdout


def test_public_card_renderer_escapes_untrusted_public_text():
    card = json.loads(FIXTURE.read_text(encoding="utf-8"))
    card["claim"]["summary"] = "<script>alert(1)</script> `breakout`"
    card["evidence"]["supporting"] = ["<img src=x onerror=alert(1)>"]
    rendered = render_public_intelligence_card_markdown(card)
    assert "<script>" not in rendered
    assert "<img" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt; 'breakout'" in rendered
    assert "&lt;img src=x onerror=alert(1)&gt;" in rendered
