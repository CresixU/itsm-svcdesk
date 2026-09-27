# ai-generated: 90% - Claude Code drafted this; the author reviewed the pass/fail accounting
"""Runs the pytest suite and prints the summary line the checker's own-tests option requires
(docs/lab1/CHECKS.md L1-STRETCH-3.01, docs/lab2/CHECKS.md L2-STRETCH-3.01): the last stdout line
must match `ITSMLAB-TESTS: passed=<n> failed=0` with n >= 10.
"""
import sys

import pytest


def main() -> int:
    counts = {"passed": 0, "failed": 0}

    class _CountingPlugin:
        def pytest_runtest_logreport(self, report):
            if report.when != "call":
                return
            if report.passed:
                counts["passed"] += 1
            elif report.failed:
                counts["failed"] += 1

    pytest.main(["-q", "tests"], plugins=[_CountingPlugin()])
    print(f"ITSMLAB-TESTS: passed={counts['passed']} failed={counts['failed']}")
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
