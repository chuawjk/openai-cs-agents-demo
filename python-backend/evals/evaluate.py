import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.judge import judge_response
from evals.runner import get_agent_response

_EVALS_DIR = os.path.dirname(__file__)


def load_test_cases() -> list[dict]:
    path = os.path.join(_EVALS_DIR, "test_cases.json")
    with open(path) as f:
        return json.load(f)


def write_results_csv(rows: list[dict], run_timestamp: str) -> str:
    subdir = os.path.join(_EVALS_DIR, "results", run_timestamp)
    os.makedirs(subdir, exist_ok=True)
    path = os.path.join(subdir, "eval_results.csv")
    fieldnames = ["id", "input", "criteria", "response", "passed", "reason", "run_timestamp"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


async def run_evaluation() -> None:
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_cases = load_test_cases()
    rows = []

    for tc in test_cases:
        print(f"Running {tc['id']}...", flush=True)
        response = await get_agent_response(tc["input"])
        verdict = judge_response(tc["input"], response, tc["criteria"])
        rows.append({
            "id": tc["id"],
            "input": tc["input"],
            "criteria": tc["criteria"],
            "response": response,
            "passed": verdict.passed,
            "reason": verdict.reason,
            "run_timestamp": run_timestamp,
        })
        status = "PASS" if verdict.passed else "FAIL"
        print(f"  {status}: {verdict.reason}")

    passed = sum(1 for r in rows if r["passed"])
    csv_path = write_results_csv(rows, run_timestamp)
    print(f"\nEvaluation complete.")
    print(f"Passed: {passed}/{len(rows)}")
    print(f"Results: {csv_path}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
