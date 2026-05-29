import json
from dataclasses import dataclass

import openai

_client = openai.OpenAI()

_SYSTEM_PROMPT = """\
You are evaluating an airline customer service chatbot response.
Given a user query, the agent's response, and a success criterion, decide whether the response meets the criterion.

Rules:
- Pass if the response is relevant, helpful, and satisfies the criterion.
- Fail if the response is off-topic, unhelpful, refuses unreasonably, or clearly misses what the criterion requires.
- Ignore minor phrasing issues — focus on whether the customer's need was addressed.

Respond with valid JSON only, no markdown:
{"pass": true, "reason": "one sentence"}
"""


@dataclass
class JudgeResult:
    passed: bool
    reason: str


def judge_response(user_input: str, response: str, criteria: str) -> JudgeResult:
    user_message = (
        f"User query: {user_input}\n\n"
        f"Agent response: {response}\n\n"
        f"Success criterion: {criteria}"
    )
    completion = _client.chat.completions.create(
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
