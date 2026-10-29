#!/usr/bin/env python3
"""
Cross-platform E2E Smoke Test for UK Wind Generation Forecast Accuracy API.

Usage:
    python scripts/smoke.py [BASE_URL]
    Example: python scripts/smoke.py http://127.0.0.1:8000
"""

import sys
import urllib.request
import urllib.error
import json

DEFAULT_BASE = "http://127.0.0.1:8000"

def run_test(name: str, url: str, expected_status: int, validate_fn) -> bool:
    print(f"Checking {name} ({url})... ", end="", flush=True)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode('utf-8'))
        except Exception:
            body = {}
    except Exception as e:
        print(f"FAILED (Connection error: {e})")
        return False

    if status != expected_status:
        print(f"FAILED (Expected HTTP {expected_status}, got {status})")
        return False

    try:
        if validate_fn(body):
            print(f"PASSED (HTTP {status})")
            return True
        else:
            print(f"FAILED (Validation condition failed on body: {body})")
            return False
    except Exception as e:
        print(f"FAILED (Validation exception: {e})")
        return False

def main() -> int:
    base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else DEFAULT_BASE
    print("=" * 60)
    print(f"Running E2E Smoke Tests against: {base}")
    print("=" * 60)

    checks = [
        (
            "Health check",
            f"{base}/api/health",
            200,
            lambda b: b.get("status") == "ok",
        ),
        (
            "Metadata window",
            f"{base}/api/meta",
            200,
            lambda b: b.get("window", {}).get("expected_periods") == 744,
        ),
        (
            "Summary metrics",
            f"{base}/api/summary?cutoff_time=09:00",
            200,
            lambda b: (
                b.get("metrics", {}).get("n_matched", 0) > 0
                and b.get("metrics", {}).get("mae_mw") is not None
            ),
        ),
        (
            "Time-series hourly",
            f"{base}/api/series?granularity=hourly",
            200,
            lambda b: isinstance(b.get("points"), list) and len(b.get("points")) > 0,
        ),
        (
            "Records pagination",
            f"{base}/api/records?page=1&page_size=50",
            200,
            lambda b: (
                isinstance(b.get("items"), list)
                and 0 < len(b.get("items")) <= 50
                and b.get("total_items", 0) > 0
            ),
        ),
        (
            "Validation error handling",
            f"{base}/api/summary?cutoff_time=99:99",
            400,
            lambda b: b.get("error", {}).get("code") == "INVALID_PARAMETER",
        ),
    ]

    all_passed = True
    for name, url, expected_status, fn in checks:
        if not run_test(name, url, expected_status, fn):
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All smoke checks passed successfully!")
        return 0
    else:
        print("Some smoke checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

