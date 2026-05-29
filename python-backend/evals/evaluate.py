import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.judge import judge_response
from evals.runner import get_agent_response


def load_test_cases() -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "test_cases.json")
    with open(path) as f:
        return json.load(f)


async def run_evaluation() -> None:
    test_cases = load_test_cases()
    results = []

    for tc in test_cases:
        print(f"Running {tc['id']}...", flush=True)
        response = await get_agent_response(tc["input"])
        verdict = judge_response(tc["input"], response, tc["criteria"])
        results.append({"id": tc["id"], "passed": verdict.passed, "reason": verdict.reason})
        status = "PASS" if verdict.passed else "FAIL"
        print(f"  {status}: {verdict.reason}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\nEvaluation complete.")
    print(f"Passed: {passed}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
