#!/usr/bin/env python3
"""
Test script for Banking Agent C: one-best-offer, churn cohort, persona-best-offer.
Run after Agent A and B have been executed (or against a running API that has already run them).

Usage:
  python tests/test_agent_c_banking.py                    # use default base_url
  python tests/test_agent_c_banking.py http://localhost:8002

Requirements:
  - Backend running with banking data loaded and Agent A (and ideally Agent B) executed.
  - Or run Agent A and B via API first, then run this script.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import requests
except ImportError:
    requests = None


def get_base_url():
    return os.environ.get("BANKING_API_BASE", "http://localhost:8002").rstrip("/")


def run_agent_a_if_needed(base_url: str) -> bool:
    """Run Agent A if status says not complete. Returns True if Agent A is complete after."""
    r = requests.get(f"{base_url}/api/banking/status")
    r.raise_for_status()
    data = r.json()
    if data.get("agent_a_complete"):
        return True
    # Execute Agent A
    r = requests.post(
        f"{base_url}/api/banking/agent_a/execute",
        json={"n_clusters": 5, "gamma": 0.5},
    )
    if r.status_code != 200:
        print(f"  Warning: Agent A execute returned {r.status_code}: {r.text[:200]}")
        return False
    print("  Agent A executed successfully.")
    return True


def test_status(base_url: str) -> bool:
    print("\n[1] GET /api/banking/status")
    r = requests.get(f"{base_url}/api/banking/status")
    if r.status_code != 200:
        print(f"  FAIL: status {r.status_code}")
        return False
    data = r.json()
    print(f"  data_loaded={data.get('data_loaded')}, agent_a_complete={data.get('agent_a_complete')}, agent_b_complete={data.get('agent_b_complete')}")
    if not data.get("agent_a_complete"):
        print("  Agent A not complete. Attempting to run Agent A...")
        if not run_agent_a_if_needed(base_url):
            print("  FAIL: Agent A could not be run. Load data and run Agent A first.")
            return False
    print("  OK")
    return True


def test_customers(base_url: str) -> Optional[str]:
    print("\n[2] GET /api/banking/agent_a/customers?limit=5")
    r = requests.get(f"{base_url}/api/banking/agent_a/customers", params={"limit": 5})
    if r.status_code != 200:
        print(f"  FAIL: status {r.status_code} - {r.text[:300]}")
        return None
    data = r.json()
    customers = data.get("data", {}).get("customers") or data.get("customers") or []
    if not customers:
        print("  FAIL: no customers in response")
        return None
    customer_id = customers[0].get("customer_id")
    print(f"  OK: got {len(customers)} customers, first id={customer_id}")
    return str(customer_id)


def test_one_best_offer(base_url: str, customer_id: str) -> bool:
    print(f"\n[3] GET /api/banking/agent_c/one-best-offer/{customer_id}")
    r = requests.get(f"{base_url}/api/banking/agent_c/one-best-offer/{customer_id}")
    if r.status_code != 200:
        print(f"  FAIL: status {r.status_code} - {r.text[:400]}")
        return False
    data = r.json()
    if not data.get("success") or "data" not in data:
        print(f"  FAIL: unexpected shape: {list(data.keys())}")
        return False
    d = data["data"]
    if d.get("offer") is None and (d.get("reason") or "").strip():
        print(f"  OK (no offer): reason={d.get('reason', '')[:80]}")
        return True
    offer = d.get("offer") or {}
    if not offer.get("product_name"):
        print(f"  FAIL: offer missing product_name: {offer}")
        return False
    print(f"  OK: offer={offer.get('product_name')}, score={d.get('score')}, reason={d.get('reason', '')[:60]}...")
    if "explainability" in d:
        print(f"  explainability keys: {list(d['explainability'].keys())}")
    if "channels" in d and d["channels"]:
        print(f"  channels: {[c.get('channel') for c in d['channels'][:3]]}")
    return True


def test_churn_cohort(base_url: str) -> bool:
    print("\n[4] GET /api/banking/churn-cohort?risk=High,Critical&limit=10")
    r = requests.get(f"{base_url}/api/banking/churn-cohort", params={"risk": "High,Critical", "limit": 10})
    if r.status_code != 200:
        print(f"  FAIL: status {r.status_code}")
        return False
    data = r.json()
    if not data.get("success"):
        print(f"  FAIL: success=False")
        return False
    cohort = data.get("cohort") or []
    total = data.get("total", 0)
    print(f"  OK: total={total}, returned={len(cohort)}")
    if cohort and len(cohort) > 0:
        first = cohort[0]
        print(f"  sample: customer_id={first.get('customer_id')}, churn_risk_score={first.get('churn_risk_score')}, category={first.get('churn_risk_category')}")
    return True


def test_persona_best_offer(base_url: str) -> bool:
    print("\n[5] GET /api/banking/agent_c/persona-best-offer?persona_id=...")
    for persona_id in (0, 1, 2):
        r = requests.get(f"{base_url}/api/banking/agent_c/persona-best-offer", params={"persona_id": persona_id})
        if r.status_code == 200:
            data = r.json()
            if not data.get("success") or "data" not in data:
                print(f"  FAIL: unexpected shape for persona_id={persona_id}")
                continue
            d = data["data"]
            print(f"  OK: persona_id={persona_id}, persona_name={d.get('persona_name')}, segment_size={d.get('segment_size')}, representative={d.get('representative_customer_id')}")
            if d.get("offer"):
                print(f"  offer: {d['offer'].get('product_name')}, score={d.get('score')}")
            return True
        if r.status_code == 404:
            detail = (r.json() or {}).get("detail", "")
            if "Persona id" in detail or "not found" in detail.lower():
                continue
            print(f"  FAIL: 404 for persona_id={persona_id}. If detail is 'Not Found' or 'API route not found', restart the backend so /api/banking/agent_c/persona-best-offer is registered.")
            print(f"  detail: {detail[:200]}")
        else:
            print(f"  FAIL: status {r.status_code} - {r.text[:300]}")
    print("  FAIL: no persona_id in (0,1,2) returned 200. Restart the backend to load the persona-best-offer route.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Test Banking Agent C endpoints")
    parser.add_argument("base_url", nargs="?", default=get_base_url(), help="API base URL (default: env BANKING_API_BASE or http://localhost:8002)")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    if requests is None:
        print("Install requests: pip install requests")
        sys.exit(1)

    print(f"Testing Agent C against {base_url}")

    ok = True
    if not test_status(base_url):
        ok = False
        print("\nAborting: status/Agent A not ready.")
        sys.exit(2)

    customer_id = test_customers(base_url)
    if not customer_id:
        ok = False
    else:
        if not test_one_best_offer(base_url, customer_id):
            ok = False
    if not test_churn_cohort(base_url):
        ok = False
    if not test_persona_best_offer(base_url):
        ok = False

    print("\n" + "=" * 60)
    if ok:
        print("All Agent C tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
