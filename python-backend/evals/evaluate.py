import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone

import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.getLogger("openai.agents").setLevel(logging.ERROR)

from evals.judge import judge_response
from evals.runner import run_agent

_EVALS_DIR = os.path.dirname(__file__)
_CSV_FIELDS = ["id", "category", "input", "criteria", "response", "passed", "reason", "run_timestamp"]


def load_test_cases() -> list[dict]:
    path = os.path.join(_EVALS_DIR, "test_cases.json")
    with open(path) as f:
        return json.load(f)


def _results_dir(run_timestamp: str) -> str:
    path = os.path.join(_EVALS_DIR, "results", run_timestamp)
    os.makedirs(path, exist_ok=True)
    return path


async def run_evaluation() -> None:
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    test_cases = load_test_cases()
    results_dir = _results_dir(run_timestamp)
    csv_path = os.path.join(results_dir, "eval_results.csv")
    jsonl_path = os.path.join(results_dir, "traces.jsonl")

    passed = 0
    with (
        open(csv_path, "w", newline="") as csv_file,
        open(jsonl_path, "w") as jsonl_file,
        tqdm.tqdm(total=len(test_cases), unit="case", ncols=80) as bar,
    ):
        writer = csv.DictWriter(csv_file, fieldnames=_CSV_FIELDS)
        writer.writeheader()

        for tc in test_cases:
            bar.set_description(tc["id"])
            output = await run_agent(tc["input"])
            verdict = judge_response(tc["input"], output.response, tc["criteria"], trace=output.trace)

            row = {
                "id": tc["id"],
                "category": tc["category"],
                "input": tc["input"],
                "criteria": tc["criteria"],
                "response": output.response,
                "passed": verdict.passed,
                "reason": verdict.reason,
                "run_timestamp": run_timestamp,
            }
            writer.writerow(row)
            csv_file.flush()

            trace = {"tc_id": tc["id"], "run_timestamp": run_timestamp, **output.trace}
            jsonl_file.write(json.dumps(trace) + "\n")
            jsonl_file.flush()

            if verdict.passed:
                passed += 1
            bar.update(1)

    print(f"\nEvaluation complete.")
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Results:  {csv_path}")
    print(f"Traces:   {jsonl_path}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
