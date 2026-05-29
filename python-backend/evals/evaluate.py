import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.judge import judge_response
from evals.runner import run_agent

_EVALS_DIR = os.path.dirname(__file__)


def load_test_cases() -> list[dict]:
    path = os.path.join(_EVALS_DIR, "test_cases.json")
    with open(path) as f:
        return json.load(f)


def _results_dir(run_timestamp: str) -> str:
    path = os.path.join(_EVALS_DIR, "results", run_timestamp)
    os.makedirs(path, exist_ok=True)
    return path


def write_results_csv(rows: list[dict], run_timestamp: str) -> str:
    path = os.path.join(_results_dir(run_timestamp), "eval_results.csv")
    fieldnames = ["id", "category", "input", "criteria", "response", "passed", "reason", "run_timestamp"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_traces_jsonl(traces: list[dict], run_timestamp: str) -> str:
    path = os.path.join(_results_dir(run_timestamp), "traces.jsonl")
    with open(path, "w") as f:
        for trace in traces:
            f.write(json.dumps(trace) + "\n")
    return path


async def run_evaluation() -> None:
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_cases = load_test_cases()
    rows = []
    traces = []

    for tc in test_cases:
        print(f"Running {tc['id']}...", flush=True)
        output = await run_agent(tc["input"])
        verdict = judge_response(tc["input"], output.response, tc["criteria"])
        rows.append({
            "id": tc["id"],
            "category": tc["category"],
            "input": tc["input"],
            "criteria": tc["criteria"],
            "response": output.response,
            "passed": verdict.passed,
            "reason": verdict.reason,
            "run_timestamp": run_timestamp,
        })
        traces.append({
            "tc_id": tc["id"],
            "run_timestamp": run_timestamp,
            **output.trace,
        })
        status = "PASS" if verdict.passed else "FAIL"
        print(f"  {status}: {verdict.reason}")

    passed = sum(1 for r in rows if r["passed"])
    csv_path = write_results_csv(rows, run_timestamp)
    jsonl_path = write_traces_jsonl(traces, run_timestamp)
    print(f"\nEvaluation complete.")
    print(f"Passed: {passed}/{len(rows)}")
    print(f"Results:  {csv_path}")
    print(f"Traces:   {jsonl_path}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
