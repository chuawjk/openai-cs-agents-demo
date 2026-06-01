import json
from dataclasses import dataclass

import openai

_client = openai.AsyncOpenAI()

_SYSTEM_PROMPT = """\
You are evaluating an airline customer service multi-agent system.
Given a user query, the full agent execution trace (tool calls, handoffs, and messages), the final response, and a success criterion, decide whether the interaction meets the criterion.

Rules:
- Pass if the final response is relevant, helpful, and satisfies the criterion.
- Use the trace to check whether the right agents were invoked, correct tools were called, and intermediate steps were sensible.
- Fail if the response is off-topic, unhelpful, refuses unreasonably, clearly misses what the criterion requires, or if the trace reveals a wrong agent path or missing tool call that undermines correctness.
- Ignore minor phrasing issues — focus on whether the customer's need was addressed end-to-end.

Respond with valid JSON only, no markdown:
{"pass": true, "reason": "one sentence"}
"""


@dataclass
class JudgeResult:
    passed: bool
    reason: str


def _format_trace(trace: dict) -> str:
    lines = [f"Final agent: {trace.get('final_agent', 'unknown')}"]
    for step in trace.get("steps", []):
        t = step.get("type")
        if t == "user_input":
            lines.append(f"[user] {step['content']}")
        elif t == "handoff":
            lines.append(f"[handoff] {step['from_agent']} → {step['to_agent']}")
        elif t == "tool_call":
            lines.append(f"[tool_call:{step['agent']}] {step['tool']}({step.get('args', '')})")
        elif t == "tool_output":
            lines.append(f"[tool_output:{step['agent']}] {step.get('output', '')[:200]}")
        elif t == "message":
            lines.append(f"[message:{step['agent']}] {step.get('content', '')[:300]}")
    usage = trace.get("usage", {})
    lines.append(f"[tokens] in={usage.get('input_tokens',0)} out={usage.get('output_tokens',0)}")
    return "\n".join(lines)


async def judge_response(user_input: str, response: str, criteria: str, trace: dict | None = None) -> JudgeResult:
    trace_section = ""
    if trace:
        trace_section = f"\nAgent execution trace:\n{_format_trace(trace)}\n"
    user_message = (
        f"User query: {user_input}\n"
        f"{trace_section}\n"
        f"Final agent response: {response}\n\n"
        f"Success criterion: {criteria}"
    )
    completion = await _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    return JudgeResult(passed=bool(data.get("pass")), reason=data.get("reason", ""))
