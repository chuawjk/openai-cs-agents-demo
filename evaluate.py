import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "python-backend"))

from agents import Runner
from airline.agents import triage_agent
from airline.context import AirlineAgentChatContext, create_initial_context
from chatkit.types import ThreadMetadata
from memory_store import MemoryStore


def load_test_cases(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def score(response: str, expected_keywords: list[str]) -> bool:
    return any(kw.lower() in response.lower() for kw in expected_keywords)


async def get_response(messages: list[dict]) -> str:
    store = MemoryStore()
    thread = ThreadMetadata(id=uuid4().hex, created_at=datetime.now())
    ctx = AirlineAgentChatContext(
        thread=thread,
        store=store,
        request_context={},
        state=create_initial_context(),
    )
    result = await Runner.run(triage_agent, messages, context=ctx)
    return result.final_output or ""


async def run_evaluation():
    test_cases = load_test_cases("test_cases.json")
    messages = []
    passed = 0

    for tc in test_cases:
        messages.append({"role": "user", "content": tc["input"]})
        response = await get_response(messages)
        messages.append({"role": "assistant", "content": response})
        if score(response, tc["expected_keywords"]):
            passed += 1

    print("Evaluation complete.")
    print(f"Passed: {passed}/{len(test_cases)}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
