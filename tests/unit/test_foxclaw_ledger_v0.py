from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest

from foxclaw.ledger.receipt_hashing import receipt_payload_hash, verify_receipt_hash
from foxclaw.ledger.receipt_models import receipt_from_coordination_packet
from foxclaw.ledger.receipt_store import ReceiptStore
from foxclaw.ledger.review_queue import ReviewQueue

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "contracts"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_coordination_packet_writes_ledger_receipt(tmp_path):
    packet = _load_fixture("coinfox_intent.valid.json")
    receipt = receipt_from_coordination_packet(packet).to_dict()
    store = ReceiptStore(tmp_path / "receipts.jsonl")

    store.append(receipt)
    receipts = store.list_receipts()

    assert len(receipts) == 1
    assert receipts[0]["receipt_id"] == "fcledger-coord-intent-001"
    assert receipts[0]["receipt_type"] == "coordination_intent"
    assert receipts[0]["status"] == "intent_recorded"
    assert receipts[0]["authority_requested"] == ["draft_only"]
    assert receipts[0]["authority_granted"] == []
    assert store.verify()[0]["valid"] is True


def test_receipt_hash_is_stable_across_key_order():
    receipt = receipt_from_coordination_packet(_load_fixture("coinfox_decision_ack.valid.json")).to_dict()
    reordered = dict(reversed(list(receipt.items())))

    assert verify_receipt_hash(receipt) is True
    assert receipt_payload_hash(reordered) == receipt["payload_hash"]


def test_tampered_receipt_fails_verification():
    receipt = receipt_from_coordination_packet(_load_fixture("coinfox_action_receipt.valid.json")).to_dict()
    tampered = dict(receipt)
    tampered["status"] = "executed_after_tamper"

    assert verify_receipt_hash(receipt) is True
    assert verify_receipt_hash(tampered) is False


def test_outcome_receipt_creates_review_task(tmp_path):
    receipt = receipt_from_coordination_packet(_load_fixture("coinfox_outcome_receipt.valid.json")).to_dict()
    queue = ReviewQueue(tmp_path / "review_tasks.jsonl")

    task = queue.create_from_receipt(receipt)
    tasks = queue.list_tasks()

    assert task is not None
    assert len(tasks) == 1
    assert tasks[0]["linked_intent_id"] == "coord-demo-001"
    assert tasks[0]["linked_receipt_id"] == "fcledger-coord-outcome-receipt-001"
    assert tasks[0]["status"] == "pending"
    assert tasks[0]["review_after"] == "2026-07-03T17:30:00Z"


def test_private_classification_is_preserved_in_receipt():
    packet = _load_fixture("coinfox_intent.valid.json")
    packet["classification"]["data_classification"] = "internal_reference_only"

    receipt = receipt_from_coordination_packet(packet)

    assert receipt.classification["data_classification"] == "internal_reference_only"
    assert receipt.classification["private_evidence_exported"] is False


def test_blocked_auto_publish_is_recorded_but_not_executed(tmp_path):
    packet = _load_fixture("coinfox_intent.blocked.json")
    receipt = receipt_from_coordination_packet(packet).to_dict()
    store = ReceiptStore(tmp_path / "receipts.jsonl")

    store.append(receipt)

    assert receipt["status"] == "blocked"
    assert receipt["authority_requested"] == ["auto_publish"]
    assert receipt["authority_granted"] == []
    assert receipt["safety"]["can_publish_to_coinfox"] is False
    assert store.verify()[0]["valid"] is True


def test_store_rejects_secret_like_receipts(tmp_path):
    receipt = receipt_from_coordination_packet(_load_fixture("coinfox_intent.valid.json")).to_dict()
    receipt["api_key"] = "sk-test-secret"
    store = ReceiptStore(tmp_path / "receipts.jsonl")

    with pytest.raises(ValueError, match="secret-like key"):
        store.append(receipt)


def test_ledger_record_demo_makes_no_live_api_calls(monkeypatch, tmp_path, capsys):
    def fail_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("network calls are forbidden in Ledger V0 demo")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    module_path = REPO / "tools" / "ledger_record_demo.py"
    spec = importlib.util.spec_from_file_location("ledger_record_demo_for_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    exit_code = module.main(
        [
            "--store",
            str(tmp_path / "receipts.jsonl"),
            "--review-queue",
            str(tmp_path / "review_tasks.jsonl"),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["receipts_written"] == 4
    assert output["review_tasks_written"] == 1
    assert output["live_api_calls"] is False
    assert output["production_writes"] is False


def test_ledger_cli_tools_round_trip(tmp_path):
    store = tmp_path / "receipts.jsonl"
    review_queue = tmp_path / "review_tasks.jsonl"
    record = subprocess.run(
        [
            sys.executable,
            "tools/ledger_record_demo.py",
            "--store",
            str(store),
            "--review-queue",
            str(review_queue),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    listed = subprocess.run(
        [sys.executable, "tools/ledger_list_receipts.py", "--store", str(store), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    verified = subprocess.run(
        [sys.executable, "tools/ledger_verify_receipt.py", "--store", str(store), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    queue = subprocess.run(
        [
            sys.executable,
            "tools/ledger_review_queue.py",
            "--review-queue",
            str(review_queue),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(record.stdout)["receipts_written"] == 4
    assert json.loads(listed.stdout)["receipt_count"] == 4
    assert json.loads(verified.stdout)["valid"] is True
    assert json.loads(queue.stdout)["task_count"] == 1
