#!/usr/bin/env python3
"""
TeamAI Test Runner
Runs all unit and integration tests
"""
import subprocess
import sys
import time

TESTS = [
    ("Department Tests", "tests/test_departments.py"),
    ("Extraction Tests", "tests/test_extraction.py"),
    ("Email Reminder Tests", "tests/test_email_reminders.py"),
    ("API Integration Tests", "tests/test_api_integration.py"),
]

def main():
    print("=" * 70)
    print("TEAMAI TEST SUITE")
    print("=" * 70)

    all_passed = True
    results = []

    for name, test_file in TESTS:
        print(f"\n{'='*70}")
        print(f"Running: {name}")
        print(f"{'='*70}\n")

        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=False
        )
        duration = time.time() - start

        passed = result.returncode == 0
        all_passed = all_passed and passed

        results.append({
            "name": name,
            "passed": passed,
            "duration": duration
        })

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status:12} {r['name']:30} ({r['duration']:.2f}s)")

    print("=" * 70)

    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
