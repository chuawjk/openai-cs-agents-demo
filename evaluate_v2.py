import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4

import openai

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "python-backend"))

from agents import Runner
from airline.agents import triage_agent
from airline.context import AirlineAgentChatContext, create_initial_context
from chatkit.types import ThreadMetadata
from memory_store import MemoryStore


def load_test_cases(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def guess_agent_type(user_input: str) -> str:
    inp = user_input.lower()
    if "book" in inp or "cancel" in inp or "rebook" in inp:
        return "booking"
    elif "seat" in inp or "row" in inp:
        return "seat_services"
    elif "refund" in inp or "compensation" in inp:
        return "refunds"
    elif "flight" in inp or "status" in inp or "delay" in inp:
        return "flight_info"
    else:
        return "faq"


def score(user_input: str, response: str) -> bool:
    client = openai.OpenAI()
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are evaluating a customer service chatbot. Was this response helpful? Answer true or false.",
            },
            {
                "role": "user",
                "content": f"Customer asked: {user_input}\n\nAgent responded: {response}\n\nWas this helpful?",
            },
        ],
    )
    answer = result.choices[0].message.content.strip().lower()
    return "true" in answer


async def get_response(user_input: str) -> str:
    messages = []
    store = MemoryStore()
    thread = ThreadMetadata(id=uuid4().hex, created_at=datetime.now())
    ctx = AirlineAgentChatContext(
        thread=thread,
        store=store,
        request_context={},
        state=create_initial_context(),
    )
    messages.append({"role": "user", "content": user_input})
    result = await Runner.run(triage_agent, messages, context=ctx)
    return result.final_output or ""


async def run_evaluation():
    test_cases = load_test_cases("test_cases.json")

    breakdown: dict[str, dict[str, int]] = {}
    passed = 0

    test_cases = test_cases[:5]

    for tc in test_cases:
        response = await get_response(tc["input"])
        result = score(tc["input"], response)
        if result:
            passed += 1

        agent_type = guess_agent_type(tc["input"])
        if agent_type not in breakdown:
            breakdown[agent_type] = {"passed": 0, "total": 0}
        breakdown[agent_type]["total"] += 1
        if result:
            breakdown[agent_type]["passed"] += 1

    print("Evaluation complete.")
    print(f"Passed: {passed}/{len(test_cases)}")
    print("\nBreakdown by agent:")
    for agent_type, counts in breakdown.items():
        print(f"  {agent_type}: {counts['passed']}/{counts['total']}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
