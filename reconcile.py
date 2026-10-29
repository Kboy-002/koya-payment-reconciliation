#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python reconcile.py   (Windows; use python3 elsewhere)
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def parse_amount(value):
    """Amounts arrive as numbers or as strings like "55,707.77"; return a float or None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def load_attempts():
    """Yield every readable event that carries a txn_id, with its line number."""
    with open(BASE_DIR / "payments.jsonl", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue  # line can't be read - ignore
            if not isinstance(event, dict):
                continue
            txn_id = event.get("txn_id")
            if not isinstance(txn_id, str) or not txn_id.strip():
                continue  # event without a txn_id - ignore
            yield event, line_no


def latest_attempts():
    """Keep only the latest attempt per txn_id (newest ts, ties broken by last line)."""
    latest = {}
    for event, line_no in load_attempts():
        order = (str(event.get("ts", "")), line_no)
        if event["txn_id"] not in latest or order > latest[event["txn_id"]][0]:
            latest[event["txn_id"]] = (order, event)
    return [event for _, event in latest.values()]


total = 0.0
count = 0

for event in latest_attempts():
    if event.get("status") != "success":
        continue
    amount = parse_amount(event.get("amount"))
    if amount is None:
        continue
    total += amount
    count += 1

with open(BASE_DIR / "expected.txt", encoding="utf-8") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
