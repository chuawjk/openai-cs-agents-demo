import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from agents import Runner
from agents.items import (
    HandoffOutputItem,
    ItemHelpers,
    MessageOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from airline.agents import triage_agent
from airline.context import AirlineAgentChatContext, create_initial_context
from chatkit.types import ThreadMetadata
from memory_store import MemoryStore


@dataclass
class RunOutput:
    response: str
    trace: dict


def _extract_steps(new_items: list, user_input: str) -> list[dict]:
    steps = [{"type": "user_input", "content": user_input}]
    for item in new_items:
        agent_name = item.agent.name if item.agent else "unknown"
        if isinstance(item, HandoffOutputItem):
            steps.append({
                "type": "handoff",
                "from_agent": item.source_agent.name if item.source_agent else "unknown",
                "to_agent": item.target_agent.name if item.target_agent else "unknown",
            })
        elif isinstance(item, ToolCallItem):
            args = getattr(item.raw_item, "arguments", None)
            steps.append({
                "type": "tool_call",
                "agent": agent_name,
                "tool": item.tool_name,
                "args": args,
            })
        elif isinstance(item, ToolCallOutputItem):
            call_id = getattr(item.raw_item, "call_id", None)
            steps.append({
                "type": "tool_output",
                "agent": agent_name,
                "call_id": call_id,
                "output": str(item.output),
            })
        elif isinstance(item, MessageOutputItem):
            steps.append({
                "type": "message",
                "agent": agent_name,
                "content": ItemHelpers.text_message_output(item),
            })
    return steps


async def run_agent(user_input: str) -> RunOutput:
    store = MemoryStore()
    thread = ThreadMetadata(id=uuid4().hex, created_at=datetime.now())
    ctx = AirlineAgentChatContext(
        thread=thread,
        store=store,
        request_context={},
        state=create_initial_context(),
    )
    result = await Runner.run(triage_agent, user_input, context=ctx)

    steps = _extract_steps(result.new_items, user_input)

    total_input = sum(r.usage.input_tokens for r in result.raw_responses if r.usage)
    total_output = sum(r.usage.output_tokens for r in result.raw_responses if r.usage)

    trace = {
        "final_agent": result.last_agent.name if result.last_agent else "unknown",
        "steps": steps,
        "usage": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        },
    }

    return RunOutput(response=result.final_output or "", trace=trace)
